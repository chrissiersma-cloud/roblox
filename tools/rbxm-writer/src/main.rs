//! Turns a JSON description of Roblox instances into a .rbxm (and optionally
//! .rbxmx) file. Property values are loosely typed, like in Rojo: the real
//! type is looked up in the Roblox reflection database.
//!
//! Usage: rbxm-writer <input.json> <output.rbxm> [output.rbxmx]
//!
//! Input: an array of instances, each
//!   { "class": "Part", "name": "Body", "id": "optional-unique-id",
//!     "props": { "Size": [1, 2, 3], "Part0": { "ref": "some-id" }, ... },
//!     "attrs": { "Role": "Fur" }, "tags": ["Animal"], "children": [ ... ] }
//!
//! UDim values are [scale, offset], UDim2 values [xScale, xOffset, yScale, yOffset]; Font values are
//! { "family": "rbxasset://fonts/families/FredokaOne.json", "weight": 700 }.

use std::{collections::HashMap, fs, fs::File, io::BufWriter};

use anyhow::{anyhow, bail, Context, Result};
use rbx_dom_weak::{
    types::{
        Attributes, CFrame, Color3, Color3uint8, ColorSequence, ColorSequenceKeypoint, Content,
        ContentId, Enum, Font, FontStyle, FontWeight, Matrix3, NumberRange, NumberSequence,
        NumberSequenceKeypoint, Ref, Tags, UDim, UDim2, Variant, VariantType, Vector2, Vector3,
    },
    ustr, InstanceBuilder, WeakDom,
};
use rbx_reflection::{DataType, ReflectionDatabase};
use serde_json::Value;

struct PendingRef {
    instance: Ref,
    property: String,
    target: String,
}

struct Builder<'a> {
    db: &'a ReflectionDatabase<'static>,
    dom: WeakDom,
    ids: HashMap<String, Ref>,
    pending: Vec<PendingRef>,
}

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        bail!("usage: rbxm-writer <input.json> <output.rbxm> [output.rbxmx]");
    }

    let input: Value = serde_json::from_str(&fs::read_to_string(&args[1])?)?;
    let nodes = input.as_array().context("input must be a JSON array")?;

    let mut builder = Builder {
        db: rbx_reflection_database::get()?,
        dom: WeakDom::new(InstanceBuilder::new("DataModel")),
        ids: HashMap::new(),
        pending: Vec::new(),
    };

    let root = builder.dom.root_ref();
    let mut top_level = Vec::new();
    for node in nodes {
        top_level.push(builder.build(root, node)?);
    }

    for pending in std::mem::take(&mut builder.pending) {
        let target = *builder
            .ids
            .get(&pending.target)
            .with_context(|| format!("unknown ref id '{}'", pending.target))?;
        builder
            .dom
            .get_by_ref_mut(pending.instance)
            .unwrap()
            .properties
            .insert(ustr(&pending.property), Variant::Ref(target));
    }

    rbx_binary::to_writer(BufWriter::new(File::create(&args[2])?), &builder.dom, &top_level)?;
    if let Some(xml_path) = args.get(3) {
        rbx_xml::to_writer_default(BufWriter::new(File::create(xml_path)?), &builder.dom, &top_level)?;
    }

    println!("Wrote {} instances", builder.dom.descendants().count() - 1);
    Ok(())
}

impl Builder<'_> {
    fn build(&mut self, parent: Ref, node: &Value) -> Result<Ref> {
        let class = node["class"].as_str().context("instance without class")?;
        let name = node["name"].as_str().unwrap_or(class);

        let mut instance = InstanceBuilder::new(class).with_name(name);
        let mut refs = Vec::new();

        if let Some(props) = node["props"].as_object() {
            for (key, value) in props {
                if let Some(target) = value.get("ref") {
                    refs.push((key.clone(), target.as_str().unwrap().to_owned()));
                    continue;
                }
                let variant = self
                    .convert(class, key, value)
                    .with_context(|| format!("{name} ({class}).{key}"))?;
                instance.add_property(key.as_str(), variant);
            }
        }

        if let Some(attrs) = node["attrs"].as_object() {
            let mut attributes = Attributes::new();
            for (key, value) in attrs {
                attributes.insert(key.clone(), attribute_value(value)?);
            }
            instance.add_property("Attributes", attributes);
        }

        if let Some(tags) = node["tags"].as_array() {
            let tags: Vec<String> = tags.iter().map(|t| t.as_str().unwrap().to_owned()).collect();
            instance.add_property("Tags", Tags::from(tags));
        }

        let referent = self.dom.insert(parent, instance);

        if let Some(id) = node["id"].as_str() {
            if self.ids.insert(id.to_owned(), referent).is_some() {
                bail!("duplicate id '{id}'");
            }
        }
        for (property, target) in refs {
            self.pending.push(PendingRef { instance: referent, property, target });
        }

        if let Some(children) = node["children"].as_array() {
            for child in children {
                self.build(referent, child)?;
            }
        }
        Ok(referent)
    }

    fn convert(&self, class: &str, property: &str, value: &Value) -> Result<Variant> {
        let class_descriptor = self
            .db
            .classes
            .get(class)
            .ok_or_else(|| anyhow!("unknown class"))?;
        let descriptor = self
            .db
            .superclasses_iter(class_descriptor)
            .find_map(|c| c.properties.get(property))
            .ok_or_else(|| anyhow!("unknown property"))?;

        let ty = match &descriptor.data_type {
            DataType::Enum(enum_name) => {
                let item = value.as_str().context("expected enum item name")?;
                let number = self.db.enums[enum_name]
                    .items
                    .get(item)
                    .with_context(|| format!("'{item}' is not in enum {enum_name}"))?;
                return Ok(Enum::from_u32(*number).into());
            }
            DataType::Value(ty) => *ty,
            _ => bail!("unsupported data type"),
        };

        let n = |i: usize| -> Result<f32> {
            value[i].as_f64().map(|v| v as f32).context("expected number array")
        };

        Ok(match ty {
            VariantType::Bool => value.as_bool().context("expected bool")?.into(),
            VariantType::Float32 => (value.as_f64().context("expected number")? as f32).into(),
            VariantType::Float64 => value.as_f64().context("expected number")?.into(),
            VariantType::Int32 => (value.as_i64().context("expected integer")? as i32).into(),
            VariantType::Int64 => value.as_i64().context("expected integer")?.into(),
            VariantType::String => value.as_str().context("expected string")?.to_owned().into(),
            VariantType::Content => Content::from_uri(value.as_str().context("expected string")?).into(),
            VariantType::ContentId => ContentId::from(value.as_str().context("expected string")?).into(),
            VariantType::Vector2 => Vector2::new(n(0)?, n(1)?).into(),
            VariantType::Vector3 => Vector3::new(n(0)?, n(1)?, n(2)?).into(),
            VariantType::Color3 => Color3::new(n(0)?, n(1)?, n(2)?).into(),
            VariantType::Color3uint8 => Color3uint8::new(
                (n(0)? * 255.0).round() as u8,
                (n(1)? * 255.0).round() as u8,
                (n(2)? * 255.0).round() as u8,
            )
            .into(),
            VariantType::CFrame => CFrame::new(
                Vector3::new(n(0)?, n(1)?, n(2)?),
                Matrix3::new(
                    Vector3::new(n(3)?, n(4)?, n(5)?),
                    Vector3::new(n(6)?, n(7)?, n(8)?),
                    Vector3::new(n(9)?, n(10)?, n(11)?),
                ),
            )
            .into(),
            VariantType::NumberRange => NumberRange::new(n(0)?, n(1)?).into(),
            // [scale, offset]
            VariantType::UDim => UDim::new(n(0)?, n(1)? as i32).into(),
            // [xScale, xOffset, yScale, yOffset]
            VariantType::UDim2 => UDim2::new(
                UDim::new(n(0)?, n(1)? as i32),
                UDim::new(n(2)?, n(3)? as i32),
            )
            .into(),
            // { "family": "rbxasset://fonts/families/FredokaOne.json", "weight": 700, "italic": false }
            VariantType::Font => {
                let family = value["family"].as_str().context("font needs a family")?;
                let weight = value["weight"].as_u64().unwrap_or(400) as u16;
                let weight = FontWeight::from_u16(weight).context("bad font weight")?;
                let style = if value["italic"].as_bool().unwrap_or(false) {
                    FontStyle::Italic
                } else {
                    FontStyle::Normal
                };
                Font::new(family, weight, style).into()
            }
            VariantType::NumberSequence => NumberSequence {
                keypoints: keypoints(value)?
                    .iter()
                    .map(|k| NumberSequenceKeypoint::new(k[0], k[1], *k.get(2).unwrap_or(&0.0)))
                    .collect(),
            }
            .into(),
            VariantType::ColorSequence => ColorSequence {
                keypoints: keypoints(value)?
                    .iter()
                    .map(|k| ColorSequenceKeypoint::new(k[0], Color3::new(k[1], k[2], k[3])))
                    .collect(),
            }
            .into(),
            other => bail!("unsupported value type {other:?}"),
        })
    }
}

fn keypoints(value: &Value) -> Result<Vec<Vec<f32>>> {
    value
        .as_array()
        .context("expected keypoint array")?
        .iter()
        .map(|k| {
            k.as_array()
                .context("expected keypoint")?
                .iter()
                .map(|v| v.as_f64().map(|v| v as f32).context("expected number"))
                .collect()
        })
        .collect()
}

fn attribute_value(value: &Value) -> Result<Variant> {
    Ok(match value {
        Value::Bool(b) => (*b).into(),
        Value::Number(n) => n.as_f64().unwrap().into(),
        Value::String(s) => s.clone().into(),
        _ => bail!("unsupported attribute value {value}"),
    })
}

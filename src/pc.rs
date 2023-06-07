//! Constructs that capture the relevant character-sheet data.
//!
//! This includes ability scores, proficiencies, and other
//! character traits. Rules for how characters interact with
//! the environment (such as darkvision) are also contained
//! here.
use json::JsonValue;
use std::collections::HashMap;
use std::fs::File;
use std::io::Read;
use std::str::FromStr;

use crate::dice::{Dice, Advantage};
use crate::environment::Lighting;

/// Ability score categories
#[derive(Eq, Hash, PartialEq)]
pub enum Ability {
    Strength,
    Dexterity,
    Constitution,
    Intelligence,
    Wisdom,
    Charisma,
}
impl FromStr for Ability {
    type Err = ();
    fn from_str(input: &str) -> Result<Ability, Self::Err> {
        match input {
            "strength" => Ok(Ability::Strength),
            "dexterity" => Ok(Ability::Dexterity),
            "constitution" => Ok(Ability::Constitution),
            "intelligence" => Ok(Ability::Intelligence),
            "wisdom" => Ok(Ability::Wisdom),
            "charisma" => Ok(Ability::Charisma),
            _ => Err(()),
        }
    }
}

/// Things which one can be proficient in
#[derive(Eq, Hash, PartialEq)]
pub enum Proficiency {
    Insight,
    Investigation,
    Perception,
}
impl FromStr for Proficiency {
    type Err = ();
    fn from_str(input: &str) -> Result<Proficiency, Self::Err> {
        match input {
            "insight"  => Ok(Proficiency::Insight),
            "investigation"  => Ok(Proficiency::Investigation),
            "perception"  => Ok(Proficiency::Perception),
            _ => Err(()),
        }
    }
}

/// A player character.
///
/// This struct is roughly equivalent to a dndbeyond character
/// sheet, in that it encapsulates the rules for rolling for
/// various checks alongside the values that numerically affect
/// the outcome.
pub struct PC<'a> {
    /// The source of randomness that a character uses to make rolls.
    dice: &'a Dice,
    /// A mapping from ability to ability score.
    abilities: HashMap<Ability, u8>,
    /// A mapping from proficiency to proficiency level.
    ///
    /// When making a roll, the PC multiplies their proficiency bonus
    /// by their proficiency level (0, 1, or 2) to determine the
    /// proficiency modifier.
    proficiencies: HashMap<Proficiency, u8>,
    /// The PC's proficiency bonus.
    proficiency_bonus: u8,
    /// Whether the PC has darkvision.
    darkvision: bool,
}

impl PC<'_> {
    /// Create a character from a configuration file.
    ///
    /// * `dice` - The dice that the PC will use to generate randomness.
    /// * `config` - A JSON configuration file which lays out the character's attributes.
    pub fn new<'a, 'b>(dice: &'a Dice, config: &'b mut File) -> std::io::Result<PC<'a>> {
        let mut abilities: HashMap<Ability, u8> = HashMap::new();
        let mut proficiencies: HashMap<Proficiency, u8> = HashMap::new();

        // Parse the file to a JSON value
        let mut config_string: String = String::new();
        config.read_to_string(&mut config_string)?;
        let config_data: JsonValue = match json::parse(&config_string) {
            Ok(data) => data,
            Err(_error) => panic!(),
        };

        // Insert each ability score into the PC's abilities.
        // Panic if they don't coerce to the enum or if their values
        // don't fit in a u8.
        for (ability, score) in config_data["abilities"].entries() {
            let ability_val: Ability = match Ability::from_str(ability) {
                Ok(data) => data,
                Err(_error) => panic!(),
            };
            let score_val: u8 = match score.as_u8() {
                Some(data) => data,
                None => panic!(),
            };
            abilities.insert(ability_val, score_val);
        }

        // Insert each proficiency into the PC's proficiencies.
        // Panic if they don't coerce to the enum or if their values
        // don't fit in a u8.
        for (proficiency, level) in config_data["proficiencies"].entries() {
            let proficiency_val: Proficiency = match Proficiency::from_str(proficiency) {
                Ok(data) => data,
                Err(_error) => panic!(),
            };
            let level_val: u8 = match level.as_u8() {
                Some(data) => data,
                None => panic!(),
            };
            proficiencies.insert(proficiency_val, level_val);
        }

        // Set the proficiency bonus.
        let proficiency_bonus: u8 = match config_data["proficiency_bonus"].as_u8() {
            Some(data) => data,
            None => panic!(),
        };

        // Set the darkvision status.
        let darkvision: bool = match config_data["darkvision"].as_bool() {
            Some(data) => data,
            None => panic!(),
        };

        Ok(PC {dice, abilities, proficiencies, proficiency_bonus, darkvision})
    }

    /// Given a profiency category, return the PC's proficiency modifier.
    ///
    /// The proficiency modifier is the PC's proficiency bonus multiplied
    /// by their level of proficiency (0, 1, or 2 for expertise).
    /// * `proficiency` - The type of proficiency whose modifier to retrieve.
    pub fn proficiency_modifier(&self, proficiency: Proficiency) -> u8 {
        self.proficiency_bonus * self.proficiencies[&proficiency]
    }

    /// Given an ability score, return the PC's ability modifier.
    /// * `ability` - The ability whose modifier to retrieve.
    pub fn ability_modifier(&self, ability: Ability) -> i8 {
        let ability_score: u8 = self.abilities[&ability];
        (ability_score as i8 - 10) / 2
    }

    /// Roll a check.
    ///
    /// Roll a d20, adding the appropriate ability and proficiency modifiers,
    /// and with the appropriate level of advantage.
    /// * `ability` - The ability to apply to the check.
    /// * `proficiency` - The proficiency to apply to the check.
    /// * `advantage` - The advantage level of the check.
    pub fn check(&mut self, ability: Ability, proficiency: Proficiency, advantage: Advantage) -> i8 {
        let proficiency_bonus: u8 = self.proficiency_modifier(proficiency);
        let ability_score: i8 = self.ability_modifier(ability);
        let total_modifier: i8 = proficiency_bonus as i8 + ability_score;

        self.dice.d(20, total_modifier, advantage)
    }

    /// Roll a Wisdom (Perception) check.
    ///
    /// Apply all available modifiers, including potential disadvantage from
    /// lighting conditions.
    /// * `advantage` - Any additional advantage beyond the usual perception parameters.
    /// * `lighting` - The level of environmental lighting.
    pub fn perception_check(&mut self, advantage: Advantage, lighting: Lighting) {
        let lighting_advantage: Advantage = match lighting {
            Lighting::Dark => if self.darkvision { Advantage::Disadvantage } else { Advantage::Fail },
            Lighting::Dim => if self.darkvision { Advantage::None } else { Advantage::Disadvantage },
            Lighting::Light => Advantage::None,
        };
        self.check(Ability::Wisdom, Proficiency::Perception, advantage + lighting_advantage);
    }
}
//! Definitions for the environment.
//!
//! The environment consists of circumstances that apply to all
//! characters in the game, and which may be passed to the
//! appropriate checks to affect their outcome.
use std::fmt;

/// Lighting affects how well characters can make vision-related checks.
///
/// Characters with darkvision will have an easier time in low-light
/// conditions.
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub enum Lighting {
    /// Characters without darkvision cannot see. Characters with
    /// darkvision see only with disadvantage.
    Dark,
    /// Characters without darkvision see only with disadvantage.
    Dim,
    /// Everyone can see without any problem.
    Light,
}

impl fmt::Display for Lighting {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let out_str: &str =
        match self {
            Lighting::Dark => "Dark Light",
            Lighting::Dim => "Dim Light",
            Lighting::Light => "Bright Light",
        };
        write!(f, "{}", out_str)
    }
}
//! Definitions for the environment.
//!
//! The environment consists of circumstances that apply to all
//! characters in the game, and which may be passed to the
//! appropriate checks to affect their outcome.

/// Lighting affects how well characters can make vision-related checks.
///
/// Characters with darkvision will have an easier time in low-light
/// conditions.
pub enum Lighting {
    /// Characters without darkvision cannot see. Characters with
    /// darkvision see only with disadvantage.
    Dark,
    /// Characters without darkvision see only with disadvantage.
    Dim,
    /// Everyone can see without any problem.
    Light,
}
//! Dice and number-generation related structs.
//!
//! This provides tools for rolling that are removed from the
//! higher-level game constructs.
use rand::{thread_rng, Rng};
use rand::rngs::ThreadRng;
use std::cmp::{max, min};
use std::cell::RefCell;
use std::ops::Add;

/// Rolls dice within given parameters.
///
/// This struct will only function in a single-threaded context.
/// To use it with multithreading, make a clone for each thread.
pub struct Dice {
    rng: RefCell<ThreadRng>,
}

/// Represents every advantage state in which a roll can be made.
pub enum Advantage {
    /// Neither advantage nor disadvantage.
    None,
    /// Advantage and disadvantage have canceled out. The roll is
    /// flat, and any additional advantage state will have no
    /// effect.
    Canceled,
    /// Roll two, take the higher.
    Advantage,
    /// Roll two, take the lower.
    Disadvantage,
    /// The roll with fail, regardless of what happens.
    Fail,
}
impl Add<Advantage> for Advantage {
    type Output = Advantage;

    /// Combine two advantage states according to the game rules.
    fn add(self, other: Advantage) -> Advantage {
        match self {
            Advantage::None => other,
            Advantage::Canceled => Advantage::Canceled,
            Advantage::Fail => Advantage::Fail,
            Advantage::Advantage => 
                match other {
                    Advantage::Advantage => Advantage::Advantage,
                    Advantage::None => Advantage::Advantage,
                    Advantage::Canceled => Advantage::Canceled,
                    Advantage::Disadvantage => Advantage::Canceled,
                    Advantage::Fail => Advantage::Fail,
                },
            Advantage::Disadvantage => 
                match other {
                    Advantage::Advantage => Advantage::Canceled,
                    Advantage::None => Advantage::Disadvantage,
                    Advantage::Canceled => Advantage::Canceled,
                    Advantage::Disadvantage => Advantage::Disadvantage,
                    Advantage::Fail => Advantage::Fail,
                },
        }
    }
}

impl Dice {
    /// Generate a new thread-locked set of dice.
    pub fn new() -> Dice {
        Dice {rng: RefCell::new(thread_rng())}
    }

    /// Roll flat, with neither advantage or disadvantage.
    ///
    /// Generally, Dice::d() should be used instead.
    ///
    /// * `d` -  The number of sides on the die.
    /// * `modifier` - The number to add to the roll.
    fn d_flat(&self, d: u8, modifier: i8) -> i8 {
        let mut borrowed_rng: std::cell::RefMut<ThreadRng> = self.rng.borrow_mut();
        let result: i8 = borrowed_rng.gen_range(1..=d) as i8 + modifier;
        log::info!("Rolling 1d{} + {} = {}", d, modifier, result);
        result
    }

    /// Roll a die with the specified advantage level.
    ///
    /// Two dice are rolled and the value used depends upon
    /// the advantage level.
    ///
    /// * `d` - The number of sides on the die.
    /// * `modifier` - The number to add to the roll.
    /// * `advantage` - The advantage level to apply.
    pub fn d(&self, d: u8, modifier: i8, advantage: Advantage) -> i8 {
        // Roll two regardless and figure out which to use later.
        let roll_1: i8 = self.d_flat(d, modifier);
        let roll_2: i8 = self.d_flat(d, modifier);
        match advantage {
            Advantage::None => roll_1,
            Advantage::Canceled => roll_1,
            Advantage::Advantage => max(roll_1, roll_2),
            Advantage::Disadvantage => min(roll_1, roll_2),
            Advantage::Fail => 0,
        }
    }
}
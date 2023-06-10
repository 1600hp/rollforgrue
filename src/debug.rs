//! A simple debug logger.
//!
//! This implementation forwards messages to the console log,
//! currently only including INFO and above messages from
//! the rollforgrue crate.

/// A simple debug logger.
///
/// This implementation forwards messages to the console log,
/// currently only including INFO and above messages from
/// the rollforgrue crate.
pub struct Debug {
}

impl log::Log for Debug {
    fn enabled(&self, metadata: &log::Metadata) -> bool {
        // TODO: Redirect non-rollforgrue messages elsewhere.
        // (Or perhaps allow them with a higher minimum severity.)
        let is_local: bool = metadata.target().starts_with("rollforgrue");
        // TODO: Make this configurable.
        is_local && metadata.level() <= log::Level::Info
    }

    fn log(&self, record: &log::Record) {
        if self.enabled(record.metadata()) {
            println!("{} - {}", record.level(), record.args());
        }
    }
    fn flush(&self) {}
}
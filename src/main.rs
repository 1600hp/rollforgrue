use iced::executor;
use iced::{Application, Command, Element, Settings, Theme};
use iced::widget::text;

mod dice;
mod environment;
mod pc;
mod debug;

static DEBUG: debug::Debug = debug::Debug {};

pub fn main() -> iced::Result {
    log::set_logger(&DEBUG).unwrap();
    log::set_max_level(log::LevelFilter::Warn);
    RollForGrue::run(Settings::default())
}

struct RollForGrue {
    dice: dice::Dice,
    last_result: i8,
}

#[derive(Debug, Clone, Copy)]
pub enum GrueMessage {
    TestMessage
}

impl RollForGrue {
}

impl Application for RollForGrue {
    type Executor = executor::Default;
    type Flags = ();
    type Message = GrueMessage;
    type Theme = Theme;

    fn new(_flags: ()) -> (RollForGrue, Command<Self::Message>) {
        let mut app: RollForGrue = RollForGrue {dice: dice::Dice::new(), last_result: 0};
        let command: Command<GrueMessage> = app.update(Self::Message::TestMessage);
        (app, command)
    }

    fn title(&self) -> String {
        String::from("Roll For Grue")
    }

    fn update(&mut self, _message: Self::Message) -> Command<Self::Message> {
        self.last_result = self.dice.d(20, 0, dice::Advantage::None);
        Command::none()
    }

    fn view(&self) -> Element<Self::Message> {
        text(format!("Hello, world! You rolled a {}.", self.last_result)).into()
    }
}
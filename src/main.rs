use iced::executor;
use iced::{Application, Command, Element, Settings, Theme};

mod dice;
mod environment;
mod pc;
mod debug;

static DEBUG: debug::Debug = debug::Debug {};

pub fn main() -> iced::Result {
    // Set up logging
    log::set_logger(&DEBUG).unwrap();
    log::set_max_level(log::LevelFilter::Info);

    // Find configuration files
    let path: Result<Option<std::path::PathBuf>, native_dialog::Error> = native_dialog::FileDialog::new()
        .show_open_single_file();

    if path.is_err() {
        log::error!("{}", path.unwrap_err());
        return Result::Ok(());
    } else {
        match path.unwrap() {
            Some(p) =>
                RollForGrue::run(Settings::with_flags((p,))),
            None => Result::Ok(()),
        }
    }
}

struct RollForGrue{
    last_result: i8,
    pcs: std::vec::Vec<pc::PC>,
}

#[derive(Debug, Clone, Copy)]
pub enum GrueMessage {
    TestMessage,
    ValueUpdated(u8)
}

impl <'a> RollForGrue {
    fn roll_slider(value: u8) -> iced::widget::Container<'a, GrueMessage, iced::Renderer> {
        let v_slider = iced::widget::vertical_slider(0u8..=30u8, value, <RollForGrue as iced::Application>::Message::ValueUpdated);
        let text = iced::widget::text(format!("{value}"));
        iced::widget::container(
            iced::widget::column![
                iced::widget::container(v_slider)
                    .width(iced::Length::Shrink)
                    .height(iced::Length::Fill).center_x(),
                iced::widget::container(text)
                    .width(iced::Length::Shrink).center_x(),
            ]
        )
    }
}

impl Application for RollForGrue {
    type Executor = executor::Default;
    type Flags = (std::path::PathBuf,);
    type Message = GrueMessage;
    type Theme = Theme;

    fn new(flags: (std::path::PathBuf,)) -> (RollForGrue, Command<Self::Message>) {
        let mut file: std::fs::File = std::fs::File::open(flags.0).expect("");
        // Set up randomness
        let mut app: RollForGrue = RollForGrue{
            last_result: 0,
            pcs: std::vec::Vec::<pc::PC>::new(),
        };

        // Add PCs
        let pc: pc::PC = pc::PC::new(&mut file).expect("");
        app.pcs.push(pc);

        let command: Command<GrueMessage> = app.update(Self::Message::TestMessage);
        (app, command)
    }

    fn title(&self) -> String {
        String::from("Roll For Grue")
    }

    fn update(&mut self, _message: Self::Message) -> Command<Self::Message> {
        self.last_result = self.pcs[0].check(pc::Ability::Wisdom, pc::Proficiency::Perception, dice::Advantage::None);
        Command::none()
    }

    fn view(&self) -> Element<Self::Message> {
        let value: u8 = self.last_result as u8;
        iced::widget::container(
            iced::widget::row![
                RollForGrue::roll_slider(value),
                RollForGrue::roll_slider(value),
                RollForGrue::roll_slider(value),
            ]
        )
        .into()
    }
}
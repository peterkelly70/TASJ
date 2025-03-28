# TASJ (Traveller's Automated System Journal)

An AI-integrated database management system for Traveller Campaigns, featuring a modern PyQt5-based GUI themed as "The Hitchhiker's Guide to the Galaxy".

## 🚀 Features

- Modern PyQt5-based GUI with light/dark theme support
- Integrated database management for campaign elements:
  - Characters
  - Ships
  - Planets
  - Organizations
  - Technology
  - Adventure hooks
  - Events
- Data download and synchronization
- Database migrations
- Customizable UI settings (theme, font)

## 🛠 Architecture

The application follows a clean MVC (Model-View-Controller) architecture:

```
TASJ/
├── model/           # Data models and database interactions
├── view/           # UI components and views
├── controller/     # Business logic and data manipulation
├── database/      # Database files and migrations
├── config/        # Configuration files
├── logs/          # Application logs
└── tests/         # Test suites
```

## 📋 Requirements

- Python 3.8+
- PyQt5
- MySQL (optional, SQLite supported by default)
- Additional dependencies in `requirements.txt`

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/TASJ.git
cd TASJ
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the environment:
```bash
cp config/.env.example config/.env
# Edit config/.env with your database settings
```

5. Run database migrations:
```bash
python main.py --migrate
```

## 🚀 Usage

1. Start the application:
```bash
python main.py
```

2. Use the menu bar to:
- Configure settings (File -> Settings)
- Download campaign data (Data -> Download All)
- Access different campaign elements (View -> Characters/Ships/etc.)

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## TODO

*   [ ] Implement Settings Dialog (`view/main_window.py`)
*   [ ] Implement Data Export functionality (`view/data_view.py`?)
*   [ ] **Integrate Google Fonts API:** Replace static `config/licenses/fonts.json` with dynamic fetching from Google Fonts API to allow browsing and installing a wider range of free fonts. Requires API key management and updates to `FontModel` and `GetMoreFontsDialog`.
*   [ ] Add error handling and user feedback for API data loading failures.
*   [ ] Refactor data loading logic for clarity and efficiency.
*   [ ] Add comprehensive unit and integration tests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Acknowledgments

- The Traveller RPG community
- PyQt5 development team
- Contributors and testers

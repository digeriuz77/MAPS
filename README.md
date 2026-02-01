# MAPS - Motivational Interviewing Practice Platform

A comprehensive training platform for practicing Motivational Interviewing (MI) techniques through interactive dialogue simulations.

## Features

### Core Training Modules
- **Persona-based Practice**: Engage with realistic characters in various scenarios
- **MAPS Competency Tracking**: Monitor progress across MI competencies
- **Real-time Feedback**: Get immediate guidance on technique usage
- **Progress Analytics**: Track improvement over time

### MI Practice Module
The MI Practice module provides structured practice scenarios for developing Motivational Interviewing skills:

- **13 Interactive Modules**: Covering focus areas like Building Rapport, Exploring Resistance, Action Planning, and more
- **Branching Dialogues**: Dynamic conversations that respond to your choices
- **Continuous Scoring**: 1-10 spectrum scoring across 5 dimensions (not binary right/wrong)
- **Technique Recognition**: Tracks use of MI-consistent techniques (reflections, open questions, affirmations)
- **Competency Alignment**: Maps to MAPS competencies (A6, B6, 1.2.1, 2.1.1, etc.)

#### MI Practice Features
- **Module Library**: Browse and filter modules by focus area and difficulty
- **Learning Paths**: Structured sequences of modules for guided learning
- **Progress Dashboard**: View completion stats, competency scores, and technique practice history
- **Attempt Review**: Analyze completed attempts with detailed feedback and learning notes
- **Personalized Recommendations**: Get module suggestions based on your progress

#### Scoring Dimensions
1. **Engagement & Rapport Building** (A6)
2. **Reflective Listening** (2.1.1, 2.1.2)
3. **Evoking Change Talk** (3.1.1, 3.2.1)
4. **Managing Resistance** (4.1.1)
5. **Therapeutic Alliance** (B6)

## Quick Start

See [MI_PRACTICE_SETUP.md](MI_PRACTICE_SETUP.md) for detailed setup instructions.

### Prerequisites
- Python 3.11+
- Supabase account
- Modern web browser

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd MAPS

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Supabase credentials

# Run database migrations
# See MI_PRACTICE_SETUP.md for migration instructions

# Seed MI modules
python scripts/seed_mi_modules.py

# Start the application
python src/main.py
```

## Project Structure

```
MAPS/
├── src/
│   ├── api/routes/mi_practice.py    # MI Practice API endpoints
│   ├── services/
│   │   ├── mi_module_service.py     # Module management
│   │   ├── mi_attempt_service.py    # Attempt lifecycle
│   │   ├── mi_scoring_service.py    # Scoring & assessment
│   │   └── mi_progress_service.py   # Progress tracking
│   └── models/mi_models.py          # Data models
├── static/
│   ├── mi-practice.html             # Module browser
│   ├── mi-practice-module.html      # Practice session
│   ├── mi-practice-review.html      # Attempt review
│   ├── mi-practice-progress.html    # Progress dashboard
│   └── js/mi-practice.js            # Frontend logic
├── tests/
│   ├── test_mi_practice.py          # Integration tests
│   └── test_mi_services.py          # Unit tests
└── scripts/
    ├── convert_mi_modules.py        # Module conversion
    └── seed_mi_modules.py           # Database seeding
```

## Documentation

- [MI_PRACTICE_SETUP.md](MI_PRACTICE_SETUP.md) - Setup and deployment guide
- [plans/mi-maps-implementation-plan.md](plans/mi-maps-implementation-plan.md) - Implementation details
- [plans/mi-maps-integration-architecture.md](plans/mi-maps-integration-architecture.md) - Architecture overview

## Testing

```bash
# Run integration tests
pytest tests/test_mi_practice.py -v

# Run unit tests
pytest tests/test_mi_services.py -v

# Run all tests
pytest tests/ -v
```

## Contributing

When adding new MI Practice modules:

1. Create module JSON in `src/data/mi_modules/`
2. Follow the naming convention: `module_X.json`
3. Include complete dialogue structure with choice points
4. Define MAPS rubric for scoring
5. Run `python scripts/seed_mi_modules.py` to add to database

## License

© VHL 2025

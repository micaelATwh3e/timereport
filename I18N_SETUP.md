# Multi-Language Support Setup

This application supports multiple languages using Flask-Babel.

## Supported Languages

Languages are **automatically discovered** from the `translations/` folder. Simply add a new language folder and it will be available immediately.

Currently available:
- **English (en)** - Default language
- **Swedish (sv)**

## How It Works

1. **Language Detection**: The app detects the user's preferred language from:
   - Session preference (if user has switched language)
   - Browser language settings
   - Falls back to English as default

2. **Language Switcher**: Users can switch languages using:
   - The dropdown in the navigation bar (when logged in)
   - Language links on the login page

3. **Translation Files**: Located in `/translations/`
   - `en.po` - English translations
   - `sv.po` - Swedish translations

## Installation

1. Install Flask-Babel:
   ```bash
   pip install Flask-Babel
   ```

2. The translations are stored in `.po` files which Flask-Babel can use directly

## For Developers: Adding New Translations

### 1. Mark text for translation in templates

Use the `_()` function in templates:
```html
<h1>{{ _('Welcome') }}</h1>
<button>{{ _('Save') }}</button>
```

### 2. Mark text for translation in Python code

```python
from flask_babel import gettext

flash(gettext('User created successfully!'), 'success')
```

### 3. Extract translatable strings

Extract all marked strings from your application:
```bash
pybabel extract -F babel.cfg -o messages.pot .
```

### 4. Add or update translation files

To update existing translations:
```bash
pybabel update -i messages.pot -d translations
```

### 5. Translate the messages

Edit the `.po` files in `translations/<language>/LC_MESSAGES/messages.po` and add translations:

```
msgid "New text to translate"
msgstr "Translation in target language"
```

### 6. Compile translations

Compile `.po` files to `.mo` for the application to use:
```bash
pybabel compile -d translations -f
```

This command compiles all translation catalogs in the `translations` directory.

## Adding a New Language

**No code changes required!** To add a new language:

1. Create the language folder structure:
   ```bash
   pybabel init -i messages.pot -d translations -l <language_code>
   ```
   Example for German:
   ```bash
   pybabel init -i messages.pot -d translations -l de
   ```

2. Translate the messages in `translations/<language_code>/LC_MESSAGES/messages.po`

3. Compile the translations:
   ```bash
   pybabel compile -d translations
   ```

4. **Restart the application** - the new language will be automatically detected and available!

The application automatically discovers all languages in the `translations/` folder that have a proper `LC_MESSAGES/` structure.

## Language Codes

- `en` - English
- `sv` - Swedish (Svenska)

## Current Language

The current language can be accessed in templates using `get_locale()`.

## Session Management

Language preference is stored in the user's session and persists across pages until:
- User switches language manually
- Session expires
- Browser is closed (if session is not permanent)

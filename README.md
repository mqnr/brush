# Brush

Brush expands upon [CanvasAPI](https://github.com/ucfopen/canvasapi), and
provides an optional limited CLI. I wrote this for my personal use during my
time using Canvas; I will likely never update it.

## Configuration

`brush.example.config.json` contains the following, and represents a valid Brush
configuration file:

```json
{
    "student_name": "John Doe",
    "course_map": [
        {
            "id": "00001",
            "aliases": ["calculus i", "calculus", "calc"]
        },
        {
            "id": "00002",
            "aliases": ["principles of macroeconomics", "macroecon"]
        }
    ]
}
```

To create your own configuration, copy the example configuration to have the
name `brush.config.json`.

```
cp brush.example.config.json brush.config.json
```

Edit the `brush.config.json` file to your liking.

## Running the CLI

The makeshift method I use is as follows:

```
git clone https://github.com/mzacuna/brush.git
cd brush
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then, I have this alias set up in my `.bashrc`:

```bash
BRUSH="/path/to/brush"
alias brush="$BRUSH/venv/bin/python $BRUSH"
```

The CLI utility is now ready for use.

```
brush --help
```

## Library usage

```python
from canvasbrush import Brush

API_URL = "https://example.instructure.com"
API_KEY = "YOUR_API_KEY"

brush = Brush(API_URL, API_KEY)

# The Brush class extends CanvasAPI's Canvas class. You can call its methods:
for course in brush.get_courses():
    print(course)
```

## License

The MIT License. See `LICENSE` for more.

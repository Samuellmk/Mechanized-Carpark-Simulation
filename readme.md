## Installation

Ensure that you have Python version >= 11.5.

cd to the directory and

```bash
source venv/bin/activate #if on unix machine
.\venv\scripts\activate.bat #if on windows machine
```

Then

```python
pip install -r requirements.txt
```

## Running the program

Define the environment variable, there are multiple Periods to choose from, see folder data/slices/

```bash
set PERIOD="6-14 Hours.csv" #example
export PERIOD="6-14 Hours.csv" #for unix machine
```

Run the program

```bash
python main.py
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)

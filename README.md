# Custom FizzBuzz style application using a block-based GUI inside tkinter.
### Alex Evans

An application that performs number replacements based on rules defined using a block based GUI.
Users can add divisors, ranges, primes and fibonacci rules to the sequence.
Matplotlib is used to display the results in a colour-coded heatmap.
Using only standard python libraries and matplotlib.

<img width="1876" height="1015" alt="image" src="https://github.com/user-attachments/assets/92b5bcd8-cf4d-4b02-9e1f-606e7af7e998" />


## Requirements

- Python 3.7+
- matplotlib
- numpy 

## Installation

1. Clone or download the project files
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python fizzbuzz_gui.py
   ```

## How to Use

1. **Launch**: Run `python fizzbuzz_gui.py`
2. **Create Blocks**: Click "+ Add Block" to create new rules, using the dropdowns to define them
3. **Run**: Set start/end numbers and click "Generate FizzBuzz"
4. **View Results**: See text output and visual heatmap

## Block Types

- **Divisor**: Replace numbers divisible by X with a word
- **Prime**: Replace prime numbers with a word  
- **Fibonacci**: Replace Fibonacci numbers with a word
- **Range**: Replace numbers in a specific range with a word

## Rule Combination

When multiple blocks match the same number, their words are combined in the order the blocks are placed (top to bottom).
For example:

- **Number 15** with Fizz(3) + Buzz(5) blocks = "FizzBuzz"
- **Number 3** with Prime + Fizz(3) blocks = "PrimeFizz" 
- **Number 13** with Prime + Fib + Range(10-20) blocks = "PrimeFibRange"


## Classes

### tkinter Classes
### BlockWidget
Defines the on screen representation of a rule block, including its buttons for editing, deleting and moving.
### BlockEditorDialog
Define the popup window for creating and editing the blocks. The window itself has to change depending on the type of rule selected (e.g. range blocks require a start and end value).
### GUI
Main application controller that controls entire GUI and coordinates with core logic.

### Other 
### BlockType
Defines types of rules that can be used.
### RuleBlock
Represents a single rule, with an ID, name, type, property and order.
### FizzBuzzResult
Contains the complete result of processing one number using all applicable rules.




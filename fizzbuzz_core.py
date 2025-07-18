# Core FizzBuzz generation engine with maths for divisors, primes, fibonacci, and ranges

import math
from typing import Set, List, Dict, Any, Tuple, Callable
from dataclasses import dataclass
from enum import Enum


class BlockType(Enum):
    DIVISOR = "divisor"
    PRIME = "prime"
    FIBONACCI = "fibonacci"
    RANGE = "range"


@dataclass
class RuleBlock:
    id: str
    block_type: BlockType
    name: str
    properties: Dict[str, Any]
    order: int = 0


@dataclass
class FizzBuzzResult:
    number: int
    text: str
    result_type: str
    matching_blocks: List[RuleBlock]


def is_prime(n: int) -> bool:
    # Check if a number is prime
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    # Check odd divisors up to sqrt(n)
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def generate_fibonacci_set(max_value: int) -> Set[int]:
    # Generate a set of Fibonacci numbers up to a maximum value
    if max_value < 1:
        return set()
    
    fibonacci_set = {1}
    a, b = 1, 1
    
    while b <= max_value:
        fibonacci_set.add(b)
        a, b = b, a + b
    
    return fibonacci_set


def process_number(number: int, blocks: List[RuleBlock], fibonacci_set: Set[int] = None) -> FizzBuzzResult:
    # Process a single number againist all rule blocks and return the result
    if fibonacci_set is None:
        fibonacci_set = set()
    
    result_parts = []
    matching_blocks = []
    
    for block in sorted(blocks, key=lambda b: b.order):
        block_matches = False
        
        if block.block_type == BlockType.DIVISOR and number % block.properties['divisor'] == 0:
            block_matches = True
        elif block.block_type == BlockType.PRIME and is_prime(number):
            block_matches = True
        elif block.block_type == BlockType.FIBONACCI and number in fibonacci_set:
            block_matches = True
        elif block.block_type == BlockType.RANGE:
            props = block.properties
            if props['start'] <= number <= props['end']:
                block_matches = True
        
        if block_matches:
            result_parts.append(block.properties['word'])
            matching_blocks.append(block)
    
    # Generate the final text result
    final_text = ''.join(result_parts) if result_parts else str(number)
    
    # Determine result type
    result_type = get_result_type(result_parts, matching_blocks)
    
    return FizzBuzzResult(
        number=number,
        text=final_text,
        result_type=result_type,
        matching_blocks=matching_blocks
    )


def get_result_type(result_parts: List[str], matching_blocks: List[RuleBlock]) -> str:
   # Determine the type of result for graphing
    if not result_parts:
        return 'number'
    elif len(matching_blocks) == 1:
        block = matching_blocks[0]
        if block.block_type == BlockType.DIVISOR:
            word = block.properties.get('word', '')
            if word == 'Fizz':
                return 'Fizz'
            elif word == 'Buzz':
                return 'Buzz'
            else:
                return 'divisor_custom'
        elif block.block_type == BlockType.PRIME:
            return 'Prime'
        elif block.block_type == BlockType.FIBONACCI:
            return 'Fib'
        elif block.block_type == BlockType.RANGE:
            return 'range_custom'
        else:
            return 'combination'
    else:
        # Multiple block matches - check for special combinations
        fizz_blocks = [b for b in matching_blocks if b.block_type == BlockType.DIVISOR and b.properties.get('word') == 'Fizz']
        buzz_blocks = [b for b in matching_blocks if b.block_type == BlockType.DIVISOR and b.properties.get('word') == 'Buzz']
        
        if fizz_blocks and buzz_blocks:
            return 'FizzBuzz'
        else:
            return 'combination'


def generate_fizzbuzz_batch(start: int, end: int, blocks: List[RuleBlock], 
                           progress_callback: Callable[[float], None] = None) -> List[FizzBuzzResult]:
    """Generate FizzBuzz results for a range of numbers with optional progress reporting."""
    if not blocks:
        raise ValueError("No blocks defined")
    if start >= end:
        raise ValueError("Start must be less than end")
    if start < 1:
        raise ValueError("Start must be at least 1")
    
    # Pre-generate Fibonacci set 
    fibonacci_set = generate_fibonacci_set(end) if any(b.block_type == BlockType.FIBONACCI for b in blocks) else set()
    
    results = []
    total_numbers = end - start + 1
    
    for i, number in enumerate(range(start, end + 1)):
        result = process_number(number, blocks, fibonacci_set)
        results.append(result)
        
        # Report progress if callback provided
        if progress_callback and ((i + 1) % 50 == 0 or i == total_numbers - 1):
            progress = (i + 1) / total_numbers * 100
            progress_callback(progress)
    
    return results

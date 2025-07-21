# GUI for fizzbuzz-based application
# using a block-based approach in tkinter and matplotlib for visualisation

import tkinter as tk
from tkinter import messagebox, ttk
from typing import List, Dict, Any, Tuple, Optional
import threading
from dataclasses import dataclass
from enum import Enum
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import ListedColormap
import matplotlib.patches as patches
import random

from fizzbuzz_core import (
    is_prime, generate_fibonacci_set, BlockType, RuleBlock, 
    FizzBuzzResult, generate_fizzbuzz_batch, process_number
)



class BlockWidget(tk.Frame):
    # On-screen representation of a rule block
    
    def __init__(self, parent, block: RuleBlock, on_edit=None, on_delete=None, on_move=None, block_color=None):
        super().__init__(parent, relief=tk.RAISED, bd=2, bg='#f0f0f0')
        
        self.block = block
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_move = on_move
        self.block_color = block_color
        
        self.setup_widget()
    
    def setup_widget(self):
        # Set up the visual elements of the block
        self.columnconfigure(1, weight=1)
        
        # Block type indicator with custom or default color
        if self.block_color:
            indicator_color = self.block_color
        else:
            # Keep special colors for Fizz and Buzz
            if self.block.block_type == BlockType.DIVISOR:
                word = self.block.properties.get('word', '')
                if word == 'Fizz':
                    indicator_color = "#3B82F6"  # Blue
                elif word == 'Buzz':
                    indicator_color = "#EF4444"  # Red
                else:
                    indicator_color = "#6B7280"  # Default gray
            else:
                type_colors = {
                    BlockType.PRIME: "#EF4444", 
                    BlockType.FIBONACCI: "#10B981",
                    BlockType.RANGE: "#F59E0B"
                }
                indicator_color = type_colors.get(self.block.block_type, "#6B7280")
        
        type_indicator = tk.Frame(self, width=8, bg=indicator_color)
        type_indicator.grid(row=0, column=0, rowspan=3, sticky="ns", padx=(5, 10), pady=5)
        
        # Block title and description
        title_text = f"{self.block.block_type.value.title()}: {self.block.name}"
        self.title_label = tk.Label(self, text=title_text, font=('Arial', 10, 'bold'), 
                                   anchor="w", bg='#f0f0f0')
        self.title_label.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(5, 0))
        
        self.desc_label = tk.Label(self, text=self.get_description(), font=('Arial', 9), 
                                  anchor="w", fg="gray", bg='#f0f0f0')
        self.desc_label.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 5))
        
        # Control buttons
        self.create_buttons()
        self.create_arrows()
    
    def get_description(self) -> str:
        # Get description of the block (For displaying on the block)
        props = self.block.properties
        try:
            if self.block.block_type == BlockType.DIVISOR:
                return f"Numbers divisible by {props['divisor']} → '{props['word']}'"
            elif self.block.block_type == BlockType.PRIME:
                return f"Prime numbers → '{props['word']}'"
            elif self.block.block_type == BlockType.FIBONACCI:
                return f"Fibonacci numbers → '{props['word']}'"
            elif self.block.block_type == BlockType.RANGE:
                return f"Numbers {props['start']}-{props['end']} → '{props['word']}'"
            else:
                return "Unknown block type"
        except KeyError as e:
            return f"Block configuration error: missing {e}"
    
    def create_buttons(self):
        # Create edit and delete buttons (For each block/rule)
        button_frame = tk.Frame(self, bg='#f0f0f0')
        button_frame.grid(row=0, column=2, rowspan=2, padx=5, pady=5)
        
        edit_btn = tk.Button(button_frame, text="Edit", width=8, height=1, 
                            command=self.on_edit_click, bg='#e0e0e0')
        edit_btn.grid(row=0, column=0, padx=2)
        
        delete_btn = tk.Button(button_frame, text="×", width=3, height=1, 
                              command=self.on_delete_click, bg='#ffcccc', fg='red')
        delete_btn.grid(row=0, column=1, padx=2)
    
    def create_arrows(self):
        # Create arrow control buttons (To move blocks up/down (Changing order of replacement))
        arrow_frame = tk.Frame(self, bg='#f0f0f0')
        arrow_frame.grid(row=0, column=3, rowspan=2, padx=5, pady=5)
        
        self.up_btn = tk.Button(arrow_frame, text="▲", width=3, height=1,
                               command=self.on_move_up, bg='#e0e0e0')
        self.up_btn.grid(row=0, column=0, pady=(0, 2))
        
        self.down_btn = tk.Button(arrow_frame, text="▼", width=3, height=1,
                                 command=self.on_move_down, bg='#e0e0e0')
        self.down_btn.grid(row=1, column=0, pady=(2, 0))

    
    # Event handlers for button clicks
    def on_edit_click(self):
        if self.on_edit:
            self.on_edit(self.block)
    
    def on_delete_click(self):
        if self.on_delete:
            self.on_delete(self.block.id)
    
    def on_move_up(self):
        if self.on_move:
            self.on_move(self.block.id, -1)
    
    def on_move_down(self):
        if self.on_move:
            self.on_move(self.block.id, 1)
    
    def update_block(self, block: RuleBlock):
        # Update the block data and refresh display
        self.block = block
        self.title_label.configure(text=f"{block.block_type.value.title()}: {block.name}")
        self.desc_label.configure(text=self.get_description())
    
    def update_arrow_states(self, is_first: bool, is_last: bool):
        # Update arrow button states based on block position (Disabled if first/last)
        self.up_btn.configure(state=tk.DISABLED if is_first else tk.NORMAL)
        self.down_btn.configure(state=tk.DISABLED if is_last else tk.NORMAL)


class BlockEditorDialog(tk.Toplevel):
    # Dialog for creating/editing rule blocks
    
    def __init__(self, parent, block: Optional[RuleBlock] = None, block_type: Optional[BlockType] = None):
        super().__init__(parent)
        
        self.result = None
        self.block = block
        self.block_type = block_type or (block.block_type if block else BlockType.DIVISOR)
        
        self.setup_dialog()
        self.populate_fields()
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        self.focus()
    
    def setup_dialog(self):
        # Set up the dialog interface
        self.title("Edit Block" if self.block else "Create Block")
        self.geometry("400x500")
        self.resizable(True, True)
        
        main_frame = tk.Frame(self, bg='white')
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = "Edit Block" if self.block else "Create New Block"
        title_label = tk.Label(main_frame, text=title, font=('Arial', 14, 'bold'), bg='white')
        title_label.pack(pady=(0, 20))
        
        # Block type selection (only for new blocks)
        if not self.block:
            self.create_type_selector(main_frame)
        
        # Properties frame
        self.props_frame = tk.Frame(main_frame, bg='white')
        self.props_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Buttons
        self.create_buttons(main_frame)
        self.setup_properties_ui()
    
    def create_type_selector(self, parent):
        # Create block type selection dropdown
        type_frame = tk.Frame(parent, bg='white')
        type_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(type_frame, text="Block Type:", bg='white').pack(anchor="w", padx=10, pady=(10, 5))
        
        self.type_var = tk.StringVar(value=self.block_type.value.title())
        type_menu = ttk.Combobox(type_frame, textvariable=self.type_var, 
                                values=[bt.value.title() for bt in BlockType],
                                state="readonly")
        type_menu.pack(fill="x", padx=10, pady=(0, 10))
        type_menu.bind('<<ComboboxSelected>>', self.on_type_change)
    
    def create_buttons(self, parent):
        # Create cancel and save buttons
        button_frame = tk.Frame(parent, bg='white')
        button_frame.pack(fill="x")
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.destroy, bg='#e0e0e0')
        cancel_btn.pack(side="right", padx=(10, 0))
        
        save_btn = tk.Button(button_frame, text="Save", command=self.save_block, bg='#4CAF50', fg='white')
        save_btn.pack(side="right")
    
    def on_type_change(self, event=None):
        # Handle block type change
        self.block_type = BlockType(self.type_var.get().lower())
        self.setup_properties_ui()
    
    def setup_properties_ui(self):
        # Set up the properties input fields based on block type
        for widget in self.props_frame.winfo_children():
            widget.destroy()
        
        # Common field: name
        tk.Label(self.props_frame, text="Name:", bg='white').pack(anchor="w", padx=10, pady=(10, 5))
        self.name_entry = tk.Entry(self.props_frame)
        self.name_entry.pack(fill="x", padx=10, pady=(0, 10))
        
        # Type-specific fields
        if self.block_type == BlockType.DIVISOR:
            self.create_divisor_fields()
        elif self.block_type in [BlockType.PRIME, BlockType.FIBONACCI]:
            self.create_word_field()
        elif self.block_type == BlockType.RANGE:
            self.create_range_fields()
    
    def create_divisor_fields(self):
        # Create divisor-specific input fields
        tk.Label(self.props_frame, text="Divisor:", bg='white').pack(anchor="w", padx=10, pady=(0, 5))
        self.divisor_entry = tk.Entry(self.props_frame)
        self.divisor_entry.pack(fill="x", padx=10, pady=(0, 10))
        self.create_word_field()
    
    def create_word_field(self):
        # Create word replacement field
        tk.Label(self.props_frame, text="Replacement Word:", bg='white').pack(anchor="w", padx=10, pady=(0, 5))
        self.word_entry = tk.Entry(self.props_frame)
        self.word_entry.pack(fill="x", padx=10, pady=(0, 10))
    
    def create_range_fields(self):
        # Create range-specific input fields
        tk.Label(self.props_frame, text="Start Number:", bg='white').pack(anchor="w", padx=10, pady=(0, 5))
        self.start_entry = tk.Entry(self.props_frame)
        self.start_entry.pack(fill="x", padx=10, pady=(0, 10))
        
        tk.Label(self.props_frame, text="End Number:", bg='white').pack(anchor="w", padx=10, pady=(0, 5))
        self.end_entry = tk.Entry(self.props_frame)
        self.end_entry.pack(fill="x", padx=10, pady=(0, 10))
        self.create_word_field()
    
    def populate_fields(self):
        # Populate fields with existing block data
        if self.block:
            self.after(10, self.do_populate_fields)
    
    def do_populate_fields(self):
        # Actually populate the fields
        if not self.block:
            return
        
        self.name_entry.insert(0, self.block.name)
        props = self.block.properties
        
        if self.block_type == BlockType.DIVISOR:
            self.divisor_entry.insert(0, str(props.get('divisor', '')))
            self.word_entry.insert(0, props.get('word', ''))
        elif self.block_type in [BlockType.PRIME, BlockType.FIBONACCI]:
            self.word_entry.insert(0, props.get('word', ''))
        elif self.block_type == BlockType.RANGE:
            self.start_entry.insert(0, str(props.get('start', '')))
            self.end_entry.insert(0, str(props.get('end', '')))
            self.word_entry.insert(0, props.get('word', ''))
    
    def save_block(self):
        # Save the block with current field values
        try:
            name = self.name_entry.get().strip()
            if not name:
                raise ValueError("Name is required")
            
            properties = self.get_properties()
            
            if 'word' in properties and not properties['word']:
                raise ValueError("Replacement word is required")
            
            # Create or update block
            import uuid
            self.result = RuleBlock(
                id=self.block.id if self.block else str(uuid.uuid4()),
                block_type=self.block_type,
                name=name,
                properties=properties,
                order=self.block.order if self.block else 0
            )
            
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
    
    def get_properties(self) -> Dict[str, Any]:
        # Extract properties based on block type
        if self.block_type == BlockType.DIVISOR:
            divisor = int(self.divisor_entry.get())
            if divisor <= 0:
                raise ValueError("Divisor must be positive")
            return {'divisor': divisor, 'word': self.word_entry.get().strip()}
        
        elif self.block_type in [BlockType.PRIME, BlockType.FIBONACCI]:
            return {'word': self.word_entry.get().strip()}
        
        elif self.block_type == BlockType.RANGE:
            start = int(self.start_entry.get())
            end = int(self.end_entry.get())
            if start >= end:
                raise ValueError("Start must be less than end")
            return {'start': start, 'end': end, 'word': self.word_entry.get().strip()}
        
        return {}


class GUI:
    # Main application
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FizzBuzz App")
        
        # Maximize the window
        self.root.state('zoomed')  
        
        # IF YOU ARE USING MAC OR LINUX UNCOMMENT THE FOLLOWING:
        # self.root.geometry("1200x800")  # Default size

        
        
        # Data
        self.blocks: List[RuleBlock] = []
        self.block_widgets: Dict[str, BlockWidget] = {}
        self.block_colors: Dict[str, str] = {}  # Map block IDs to colors
        self.is_generating = False
        
        # Cleanup
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
        self.create_default_blocks()
    
    def setup_ui(self):
        # Set up the main user interface
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        self.setup_left_panel()
        self.setup_right_panel()
    
    def setup_left_panel(self):
        # Set up the left panel (where users create and manage blocks)
        left_panel = tk.Frame(self.root, width=500, bg='#f8f9fa')
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left_panel.grid_propagate(False)
        left_panel.grid_rowconfigure(2, weight=1) 
        
        # Add title and aadd button
        header_frame = tk.Frame(left_panel, bg='#f8f9fa')
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 2))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = tk.Label(header_frame, text="Rule Blocks", font=('Arial', 16, 'bold'), 
                              bg='#f8f9fa')
        title_label.grid(row=0, column=0, sticky="w")
        
        add_btn = tk.Button(header_frame, text="+ Add Rule Block", command=self.add_block, 
                           width=12, bg='#4CAF50', fg='white')
        add_btn.grid(row=0, column=1, padx=(10, 0))
        
        # Block workspace 
        self.create_workspace(left_panel)
        
        # Action buttons
        self.create_action_buttons(left_panel)
    
    def create_workspace(self, parent):
        # Create scrollable workspace for blocks
        workspace_label = tk.Label(parent, text="Use arrows to reorder blocks and dictate order of replacement text", 
                                  font=('Arial', 9), fg='gray', bg='#f8f9fa')
        workspace_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 2))
        
        # Create canvas and scrolling
        canvas = tk.Canvas(parent, bg='white')
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.workspace_frame = tk.Frame(canvas, bg='white')
        
        self.workspace_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.workspace_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        scrollbar.grid(row=2, column=1, sticky="ns", pady=(0, 10))
        
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_columnconfigure(0, weight=1)
    
    def create_action_buttons(self, parent):
        # Create clear button
        action_frame = tk.Frame(parent, bg='#f8f9fa')
        action_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        
        clear_btn = tk.Button(action_frame, text="Clear All", command=self.clear_all_blocks, 
                             bg='#f44336', fg='white', width=10)
        clear_btn.pack(side="left", padx=(0, 10))
    
    def setup_right_panel(self):
        # Set up the right panel with configuration and results
        right_panel = tk.Frame(self.root, bg='#f8f9fa')
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right_panel.grid_rowconfigure(2, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        self.create_config_section(right_panel)
        self.create_progress_bar(right_panel)
        self.create_results_section(right_panel)
        self.create_status_bar(right_panel)
    
    def create_config_section(self, parent):
        # Create configuration section
        config_frame = tk.Frame(parent, bg='white', relief=tk.RAISED, bd=1)
        config_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        config_frame.grid_columnconfigure(1, weight=1)
        
        config_title = tk.Label(config_frame, text="Results", font=('Arial', 14, 'bold'), 
                               bg='white')
        config_title.grid(row=0, column=0, columnspan=4, pady=(10, 15))
        
        # Range inputs
        tk.Label(config_frame, text="Start:", bg='white').grid(row=1, column=0, padx=(10, 5), pady=5, sticky="w")
        self.start_entry = tk.Entry(config_frame, width=10)
        self.start_entry.insert(0, "1")
        self.start_entry.grid(row=1, column=1, padx=(0, 20), pady=5, sticky="w")
        
        tk.Label(config_frame, text="End:", bg='white').grid(row=1, column=2, padx=(0, 5), pady=5, sticky="w")
        self.end_entry = tk.Entry(config_frame, width=10)
        self.end_entry.insert(0, "100")
        self.end_entry.grid(row=1, column=3, padx=(0, 10), pady=5, sticky="w")
        
        # Generate button
        self.generate_btn = tk.Button(config_frame, text="Generate FizzBuzz", 
                                     command=self.generate_fizzbuzz, height=2, 
                                     bg='#4CAF50', fg='white')
        self.generate_btn.grid(row=2, column=0, columnspan=4, padx=10, pady=(10, 15), sticky="ew")
    
    def create_progress_bar(self, parent):
        # Create progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(parent, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
    
    def create_results_section(self, parent):
        # Create results display section
        results_frame = tk.Frame(parent, bg='white', relief=tk.RAISED, bd=1)
        results_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        results_frame.grid_rowconfigure(1, weight=1)
        results_frame.grid_columnconfigure(0, weight=1) 
        results_frame.grid_columnconfigure(1, weight=3)  
        
        # Results header
        results_header = tk.Frame(results_frame, bg='white')
        results_header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        results_header.grid_columnconfigure(0, weight=1)
        
        results_title = tk.Label(results_header, text="Results", font=('Arial', 14, 'bold'), 
                                bg='white')
        results_title.grid(row=0, column=0, sticky="w")
        
        # Results text area (Printout of text)
        text_frame = tk.Frame(results_frame)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        self.results_text = tk.Text(text_frame, font=('Consolas', 10))
        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=text_scrollbar.set)
        
        self.results_text.grid(row=0, column=0, sticky="nsew")
        text_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Heatmap section (Visual representation of results)
        self.create_heatmap_section(results_frame)
    
    def create_heatmap_section(self, parent):
        # Create matplotlib "heatmap" style of results
        heatmap_frame = tk.Frame(parent, bg='white')
        heatmap_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(0, 10))
        heatmap_frame.grid_rowconfigure(1, weight=1)
        heatmap_frame.grid_columnconfigure(0, weight=1)
        
        heatmap_title = tk.Label(heatmap_frame, text="Visual Map", font=('Arial', 12, 'bold'), 
                                bg='white')
        heatmap_title.grid(row=0, column=0, pady=(10, 5))
        
        # Create canvas for scrollable heatmap
        canvas = tk.Canvas(heatmap_frame, bg='white')
        h_scrollbar = ttk.Scrollbar(heatmap_frame, orient="horizontal", command=canvas.xview)
        v_scrollbar = ttk.Scrollbar(heatmap_frame, orient="vertical", command=canvas.yview)
        
        self.heatmap_scroll_frame = tk.Frame(canvas, bg='white')
        
        self.heatmap_scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.heatmap_scroll_frame, anchor="nw")
        canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        canvas.grid(row=1, column=0, sticky="nsew")
        h_scrollbar.grid(row=2, column=0, sticky="ew")
        v_scrollbar.grid(row=1, column=1, sticky="ns")
        
        # Create matplotlib figure and canvas
        self.heatmap_fig, self.heatmap_ax = plt.subplots(figsize=(6, 6), facecolor='white')
        self.heatmap_canvas = FigureCanvasTkAgg(self.heatmap_fig, self.heatmap_scroll_frame)
        self.heatmap_canvas.get_tk_widget().pack(padx=5, pady=5)
        
        # Initialize empty heatmap
        self.heatmap_ax.set_title("FizzBuzz Heatmap", fontsize=12, fontweight='bold', pad=20)
        self.heatmap_ax.text(0.5, 0.5, "Generate results to see heatmap", 
                            ha='center', va='center', transform=self.heatmap_ax.transAxes,
                            fontsize=10, color='gray')
        self.heatmap_ax.set_xticks([])
        self.heatmap_ax.set_yticks([])
        self.heatmap_canvas.draw()
    
    def create_status_bar(self, parent):
        # Create status bar
        self.status_label = tk.Label(parent, text="Ready", anchor="w", bg='#f8f9fa', 
                                    relief=tk.SUNKEN, bd=1)
        self.status_label.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
    
    def create_default_blocks(self):
        # Create default Fizz and Buzz blocks
        import uuid
        
        fizz_id = str(uuid.uuid4())
        buzz_id = str(uuid.uuid4())
        
        self.blocks = [
            RuleBlock(fizz_id, BlockType.DIVISOR, "Fizz", {'divisor': 3, 'word': 'Fizz'}, 0),
            RuleBlock(buzz_id, BlockType.DIVISOR, "Buzz", {'divisor': 5, 'word': 'Buzz'}, 1)
        ]
        
        # Assign default colors
        self.block_colors[fizz_id] = "#3B82F6"  # Blue for Fizz
        self.block_colors[buzz_id] = "#EF4444"  # Red for Buzz
        
        self.refresh_workspace()
    
    def generate_random_color(self) -> str:
        # Generate a random bright color (avoiding gray tones)
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", 
                  "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
                  "#F8C471", "#82E0AA", "#F1948A", "#85CEBC", "#D7BDE2"]
        return random.choice(colors)
    
    def assign_block_color(self, block: RuleBlock) -> str:
        # Assign color to block, keeping Fizz blue and Buzz red
        if block.block_type == BlockType.DIVISOR:
            word = block.properties.get('word', '')
            if word == 'Fizz':
                return "#3B82F6"  # Blue
            elif word == 'Buzz':
                return "#EF4444"  # Red
        
        # Generate random color for other blocks
        color = self.generate_random_color()
        while color in self.block_colors.values():  # Avoid duplicates
            color = self.generate_random_color()
        return color
    
    def refresh_workspace(self):
        # Refresh the workspace (Done after adding/deleting/editing or moving blocks)
        for widget in self.block_widgets.values():
            widget.destroy()
        self.block_widgets.clear()
        
        sorted_blocks = sorted(self.blocks, key=lambda b: b.order)
        
        for i, block in enumerate(sorted_blocks):
            # Assign color if not already assigned
            if block.id not in self.block_colors:
                self.block_colors[block.id] = self.assign_block_color(block)
            
            widget = BlockWidget(self.workspace_frame, block, self.edit_block, 
                               self.delete_block, self.move_block, self.block_colors[block.id])
            widget.pack(fill="x", padx=5, pady=2)
            self.block_widgets[block.id] = widget
            
            # Update arrow button states
            widget.update_arrow_states(i == 0, i == len(sorted_blocks) - 1)
        
        # Update status display
        block_count = len(self.blocks)
        self.set_status(f"Ready • {block_count} blocks configured")
    
    def add_block(self):
        # Add a new block
        dialog = BlockEditorDialog(self.root)
        self.root.wait_window(dialog)
        
        if dialog.result:
            dialog.result.order = len(self.blocks)
            self.blocks.append(dialog.result)
            self.refresh_workspace()
    
    def edit_block(self, block: RuleBlock):
        # Edit an existing block
        dialog = BlockEditorDialog(self.root, block)
        self.root.wait_window(dialog)
        
        if dialog.result:
            for i, b in enumerate(self.blocks):
                if b.id == block.id:
                    self.blocks[i] = dialog.result
                    break
            self.refresh_workspace()
    
    def delete_block(self, block_id: str):
        # Delete a block
        self.blocks = [b for b in self.blocks if b.id != block_id]
        # Remove color mapping
        if block_id in self.block_colors:
            del self.block_colors[block_id]
        self.reorder_blocks()
        self.refresh_workspace()
    
    def move_block(self, block_id: str, direction: int):
        # Move a block up or down
        block_index = next(i for i, b in enumerate(self.blocks) if b.id == block_id)
        
        if direction < 0 and block_index > 0:  # Move up
            self.blocks[block_index], self.blocks[block_index - 1] = self.blocks[block_index - 1], self.blocks[block_index]
            self.reorder_blocks()
            self.refresh_workspace()
        elif direction > 0 and block_index < len(self.blocks) - 1:  # Move down
            self.blocks[block_index], self.blocks[block_index + 1] = self.blocks[block_index + 1], self.blocks[block_index]
            self.reorder_blocks()
            self.refresh_workspace()
    
    def reorder_blocks(self):
        # Update order values for all blocks
        for i, block in enumerate(self.blocks):
            block.order = i
    
    def clear_all_blocks(self):
        # Clear all blocks
        self.blocks.clear()
        self.block_colors.clear()  # Clear color mappings
        self.refresh_workspace()
    
    def generate_fizzbuzz(self):
        # Generate FizzBuzz results based on current blocks
        if self.is_generating:
            return
        
        try:
            start = int(self.start_entry.get())
            end = int(self.end_entry.get())
            
            if start >= end:
                raise ValueError("Start must be less than end")
            if start < 1:
                raise ValueError("Start must be at least 1")
            if not self.blocks:
                raise ValueError("No blocks defined")
            
            self.is_generating = True
            self.generate_btn.configure(text="Generating...", state=tk.DISABLED)
            self.progress_var.set(0)
            
            # Run generation in separate thread
            thread = threading.Thread(target=self.generate_worker, args=(start, end))
            thread.daemon = True
            thread.start()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
    
    def generate_worker(self, start: int, end: int):
        # Worker thread for FizzBuzz generation using core functions
        try:
            # Clear results and heatmap
            self.root.after(0, self.clear_display)
            
            # Use core generation function with progress callback
            def progress_callback(progress):
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
            
            # Generate all results using the core function
            fizzbuzz_results = generate_fizzbuzz_batch(start, end, self.blocks, progress_callback)
            
            # Convert results for display
            text_results = []
            heatmap_data = []
            
            for result in fizzbuzz_results:
                text_results.append(f"{result.number:4d}: {result.text}")
                heatmap_data.append((result.number, result.text, result.result_type))
                
                # Update display periodically
                if len(text_results) >= 50:
                    self.root.after(0, lambda r=text_results.copy(): self.update_results_display(r))
                    text_results.clear()
            
            # Update any remaining results
            if text_results:
                self.root.after(0, lambda r=text_results: self.update_results_display(r))
            
            # Create heatmap and finalize
            total_numbers = len(fizzbuzz_results)
            self.root.after(0, lambda: self.finalize_generation(heatmap_data, total_numbers))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Generation failed: {str(e)}"))
        finally:
            self.root.after(0, self.generation_complete)
    
    def update_results_display(self, new_results: List[str]):
        # Update results text display with new results
        for result in new_results:
            self.results_text.insert(tk.END, result + '\n')
        self.results_text.see(tk.END)
    
    def clear_display(self):
        # Clear results text and heatmap
        self.results_text.delete("1.0", tk.END)
        self.clear_heatmap()
    
    def update_progress_and_results(self, progress: float, new_results: List[str]):
        # Update progress bar and results display
        self.progress_var.set(progress)
        for result in new_results:
            self.results_text.insert(tk.END, result + '\n')
        self.results_text.see(tk.END)
    
    def finalize_generation(self, heatmap_data: List[Tuple[int, str, str]], total_numbers: int):
        # Create heatmap and set completion status
        self.create_heatmap(heatmap_data)
        self.set_status(f"Generated {total_numbers} results")
    
    def generation_complete(self):
        # Handle completion of generation
        self.is_generating = False
        self.generate_btn.configure(text="Generate FizzBuzz", state=tk.NORMAL)
        self.progress_var.set(100)
    
    def create_heatmap(self, results_data: List[Tuple[int, str, str]]):
        # Create a professional matplotlib heatmap visualization
        self.clear_heatmap()
        
        if not results_data:
            return
        
        # Handle all datasets without sampling
        total_numbers = len(results_data)
        display_data = results_data
        
        # Always create a square grid
        grid_size = int(np.ceil(np.sqrt(total_numbers)))
        cols = grid_size
        rows = grid_size
        
        # Keep figure size constant regardless of grid size
        # This ensures the heatmap always takes the same visual space
        figure_size = 6  # Fixed size for consistent visual appearance
        self.heatmap_fig.set_size_inches(figure_size, figure_size)
        
        # Create 2D array for heatmap data
        heatmap_data = np.full((rows, cols), -1, dtype=int)  # -1 for empty cells
        
        # Fill the grid with data
        for i, (number, result, result_type) in enumerate(display_data):
            row = i // cols
            col = i % cols
            if row < rows and col < cols:
                heatmap_data[row, col] = self.get_type_value(result_type)
        
        # Create custom colormap
        colors, type_labels = self.get_colors_and_labels()
        cmap = ListedColormap(colors)
        
        # Create the heatmap
        im = self.heatmap_ax.imshow(heatmap_data, cmap=cmap, aspect='equal', 
                                   vmin=0, vmax=len(colors)-1, interpolation='nearest')
        
        # Customize the plot
        title = f"FizzBuzz Heatmap ({len(results_data)} numbers)"
        self.heatmap_ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
        self.heatmap_ax.set_xlim(-0.5, cols-0.5)
        self.heatmap_ax.set_ylim(rows-0.5, -0.5)  # Invert y-axis for top-to-bottom reading
        
        # Remove ticks and add subtle grid
        self.heatmap_ax.set_xticks([])
        self.heatmap_ax.set_yticks([])
        
        # Add grid lines
        for i in range(cols + 1):
            self.heatmap_ax.axvline(i - 0.5, color='white', linewidth=1)
        for i in range(rows + 1):
            self.heatmap_ax.axhline(i - 0.5, color='white', linewidth=1)
        
        # Create custom legend
        self.create_matplotlib_legend(type_labels)
        
        # Refresh the canvas
        self.heatmap_fig.tight_layout()
        self.heatmap_canvas.draw()
    
    def get_type_value(self, result_type: str) -> int:
        # Map result types to numeric values based on current blocks and core result types
        if result_type == 'number':
            return 0
        
        # Find the correct index by matching against the actual block order
        value = 1  # Start at 1 (after numbers at index 0)
        for block in sorted(self.blocks, key=lambda b: b.order):
            word = block.properties.get('word', '')
            
            # Check if this block matches the result type
            if ((result_type == 'Fizz' and word == 'Fizz') or
                (result_type == 'Buzz' and word == 'Buzz') or
                (result_type == 'Prime' and block.block_type == BlockType.PRIME) or
                (result_type == 'Fib' and block.block_type == BlockType.FIBONACCI) or
                (result_type == 'divisor_custom' and block.block_type == BlockType.DIVISOR and word not in ['Fizz', 'Buzz']) or
                (result_type == 'range_custom' and block.block_type == BlockType.RANGE)):
                return value
            value += 1
        
        # Handle specific FizzBuzz case
        if result_type == 'FizzBuzz' and self.has_fizz_and_buzz():
            return len(self.blocks) + 1
        
        # Others combination
        if result_type == 'combination':
            return len(self.blocks) + 2
        
        # Fallback just incase
        return len(self.blocks) + 2
    
    def get_block_color_for_result(self, result_type: str) -> str:
        # Get block color based on result type
        if result_type == 'Fizz':
            return "#3B82F6"  # Blue
        elif result_type == 'Buzz':
            return "#EF4444"  # Red
        elif result_type == 'FizzBuzz':
            return "#8B5CF6"  # Purple for fizzbuzz combination
        
        # For other types, find matching block
        for block in self.blocks:
            word = block.properties.get('word', '')
            if word == result_type and block.id in self.block_colors:
                return self.block_colors[block.id]
        
        # Default colors for special types
        if result_type == 'combination':
            return "#FF2ED9"  # Pink
        elif result_type == 'number':
            return "#E5E7EB"  # Light gray
        
        return "#6B7280"  # Default gray
    
    def get_colors_and_labels(self) -> Tuple[List[str], List[str]]:
        # Get colour mapping and labels using block colours, matching core result types
        colors = []
        labels = []
        
        # Add number colour (always first - index 0)
        colors.append("#E5E7EB")
        labels.append("Numbers")
        
        # Add colours for active blocks in order (indices 1, 2, 3, ...)
        for block in sorted(self.blocks, key=lambda b: b.order):
            word = block.properties.get('word', '')
            if word and block.id in self.block_colors:
                colors.append(self.block_colors[block.id])
                # Use the actual word as the label
                if block.block_type == BlockType.PRIME:
                    labels.append(f"Prime ({word})")
                elif block.block_type == BlockType.FIBONACCI:
                    labels.append(f"Fib ({word})")
                else:
                    labels.append(word)
        
        # Add FizzBuzz combination color (index len(blocks) + 1)
        if self.has_fizz_and_buzz():
            colors.append("#8B5CF6")  # Purple for FizzBuzz
            labels.append("FizzBuzz")
        
        # Add general combination colour (index len(blocks) + 2)
        if len(self.blocks) > 1:
            colors.append("#FF2ED9")  # Pink for other combinations
            labels.append("Combinations")
        
        return colors, labels
    
    def create_matplotlib_legend(self, type_labels: List[str]):
        # Create a simple legend for the matplotlib heatmap using actual block colors and labels
        colors, labels = self.get_colors_and_labels()
        
        # Create legend patches for all active types
        legend_elements = []
        for color, label in zip(colors, labels):
            legend_elements.append(patches.Rectangle((0, 0), 1, 1, facecolor=color, label=label))
        
        # Position legend below the plot
        if legend_elements:
            self.heatmap_ax.legend(handles=legend_elements, loc='upper center', 
                                 bbox_to_anchor=(0.5, -0.05), ncol=3, fontsize=9)
    
    def clear_heatmap(self):
        # Clear the matplotlib heatmap display
        self.heatmap_ax.clear()
        self.heatmap_ax.set_title("FizzBuzz Heatmap", fontsize=12, fontweight='bold', pad=20)
        self.heatmap_ax.set_xticks([])
        self.heatmap_ax.set_yticks([])
        
        # Remove any existing legend
        legend = self.heatmap_ax.get_legend()
        if legend:
            legend.remove()
    
    def has_fizz_and_buzz(self):
        # Check if we have both Fizz and Buzz blocks
        has_fizz = any(b.properties.get('word') == 'Fizz' for b in self.blocks if b.block_type == BlockType.DIVISOR)
        has_buzz = any(b.properties.get('word') == 'Buzz' for b in self.blocks if b.block_type == BlockType.DIVISOR)
        return has_fizz and has_buzz
    
    def set_status(self, message: str):
        # Set status message
        self.status_label.configure(text=message)
    
    def on_closing(self):
        # Clean up and close the application properly
        try:
            # Close matplotlib figure to free resources
            if hasattr(self, 'heatmap_fig'):
                plt.close(self.heatmap_fig)
        except:
            pass
        
        # Destroy the root window and exit
        self.root.destroy()
        self.root.quit()
    
    def run(self):
        # Start the application
        self.root.mainloop()


def main():
    # Main entry point for the application
    try:
        app = GUI()
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        # Ensure clean exit
        import sys
        sys.exit(0)


if __name__ == "__main__":
    main()

"""
Theme utilities for the StormShadow GUI.

This module provides modern theming capabilities for the Tkinter interface.
"""

import tkinter as tk
from tkinter import ttk


def apply_modern_theme(root: tk.Tk):
    """
    Apply a modern theme to the Tkinter application.
    
    Args:
        root: The root Tkinter window
    """
    # Configure the root window
    root.configure(bg='#2b2b2b')
    
    # Create a modern style
    style = ttk.Style()
    style.theme_use('clam')
    
    # Configure modern colors
    colors = {
        'bg': '#2b2b2b',           # Dark background
        'fg': '#ffffff',           # White text
        'select_bg': '#404040',    # Darker selection background
        'select_fg': '#ffffff',    # White selection text
        'entry_bg': '#404040',     # Entry background
        'button_bg': '#404040',    # Button background
        'active_bg': '#505050',    # Active/hover background
        'accent': '#0078d4',       # Accent color (blue)
        'success': '#107c10',      # Success color (green)
        'warning': '#ff8c00',      # Warning color (orange)
        'error': '#d13438',        # Error color (red)
        'border': '#555555',       # Border color
    }
    
    # Configure ttk styles
    
    # Frame styles
    style.configure('TFrame', background=colors['bg'])
    style.configure('Card.TFrame', background=colors['select_bg'], relief='flat', borderwidth=1)
    
    # Label styles
    style.configure('TLabel', background=colors['bg'], foreground=colors['fg'])
    style.configure('Title.TLabel', background=colors['bg'], foreground=colors['fg'], 
                   font=('Segoe UI', 14, 'bold'))
    style.configure('Heading.TLabel', background=colors['bg'], foreground=colors['fg'], 
                   font=('Segoe UI', 12, 'bold'))
    style.configure('Success.TLabel', background=colors['bg'], foreground=colors['success'])
    style.configure('Warning.TLabel', background=colors['bg'], foreground=colors['warning'])
    style.configure('Error.TLabel', background=colors['bg'], foreground=colors['error'])
    
    # Button styles
    style.configure('TButton', 
                   background=colors['button_bg'], 
                   foreground=colors['fg'],
                   borderwidth=1,
                   focuscolor='none',
                   relief='flat')
    style.map('TButton',
              background=[('active', colors['active_bg']),
                         ('pressed', colors['select_bg'])])
    
    # Primary button style
    style.configure('Primary.TButton', 
                   background=colors['accent'], 
                   foreground='white',
                   borderwidth=0,
                   focuscolor='none')
    style.map('Primary.TButton',
              background=[('active', '#106ebe'),
                         ('pressed', '#005a9e')])
    
    # Success button style
    style.configure('Success.TButton', 
                   background=colors['success'], 
                   foreground='white',
                   borderwidth=0,
                   focuscolor='none')
    style.map('Success.TButton',
              background=[('active', '#0e6e0e'),
                         ('pressed', '#0c5d0c')])
    
    # Warning button style
    style.configure('Warning.TButton', 
                   background=colors['warning'], 
                   foreground='white',
                   borderwidth=0,
                   focuscolor='none')
    style.map('Warning.TButton',
              background=[('active', '#e67c00'),
                         ('pressed', '#cc6f00')])
    
    # Danger button style
    style.configure('Danger.TButton', 
                   background=colors['error'], 
                   foreground='white',
                   borderwidth=0,
                   focuscolor='none')
    style.map('Danger.TButton',
              background=[('active', '#bc2e32'),
                         ('pressed', '#a7282c')])
    
    # Entry styles
    style.configure('TEntry', 
                   fieldbackground=colors['entry_bg'], 
                   background=colors['entry_bg'],
                   foreground=colors['fg'],
                   borderwidth=1,
                   insertcolor=colors['fg'])
    style.map('TEntry',
              focuscolor=[('!focus', colors['border']),
                         ('focus', colors['accent'])])
    
    # Combobox styles
    style.configure('TCombobox', 
                   fieldbackground=colors['entry_bg'], 
                   background=colors['entry_bg'],
                   foreground=colors['fg'],
                   borderwidth=1,
                   arrowcolor=colors['fg'])
    style.map('TCombobox',
              focuscolor=[('!focus', colors['border']),
                         ('focus', colors['accent'])],
              fieldbackground=[('readonly', colors['entry_bg'])])
    
    # Notebook styles
    style.configure('TNotebook', background=colors['bg'], borderwidth=0)
    style.configure('TNotebook.Tab', 
                   background=colors['button_bg'], 
                   foreground=colors['fg'],
                   padding=(20, 10),
                   borderwidth=1)
    style.map('TNotebook.Tab',
              background=[('selected', colors['accent']),
                         ('active', colors['active_bg'])])
    
    # Progressbar styles
    style.configure('TProgressbar', 
                   background=colors['accent'], 
                   troughcolor=colors['select_bg'],
                   borderwidth=0,
                   lightcolor=colors['accent'],
                   darkcolor=colors['accent'])
    
    # Treeview styles
    style.configure('TTreeview', 
                   background=colors['entry_bg'], 
                   foreground=colors['fg'],
                   fieldbackground=colors['entry_bg'],
                   borderwidth=1)
    style.map('TTreeview',
              background=[('selected', colors['accent'])],
              foreground=[('selected', 'white')])
    
    # Treeview heading style
    style.configure('Treeview.Heading',
                   background=colors['button_bg'],
                   foreground=colors['fg'],
                   borderwidth=1)
    style.map('Treeview.Heading',
              background=[('active', colors['active_bg'])])
    
    # Scale/Slider styles
    style.configure('TScale',
                   background=colors['bg'],
                   troughcolor=colors['entry_bg'],
                   borderwidth=1,
                   slidercolor=colors['accent'])
    
    # Checkbutton styles
    style.configure('TCheckbutton',
                   background=colors['bg'],
                   foreground=colors['fg'],
                   focuscolor='none',
                   borderwidth=0)
    style.map('TCheckbutton',
              background=[('active', colors['bg'])],
              indicatorcolor=[('selected', colors['accent']),
                            ('!selected', colors['entry_bg'])])
    
    # Radiobutton styles
    style.configure('TRadiobutton',
                   background=colors['bg'],
                   foreground=colors['fg'],
                   focuscolor='none',
                   borderwidth=0)
    style.map('TRadiobutton',
              background=[('active', colors['bg'])],
              indicatorcolor=[('selected', colors['accent']),
                            ('!selected', colors['entry_bg'])])
    
    # Scrollbar styles
    style.configure('TScrollbar',
                   background=colors['button_bg'],
                   troughcolor=colors['bg'],
                   borderwidth=0,
                   arrowcolor=colors['fg'])
    style.map('TScrollbar',
              background=[('active', colors['active_bg'])])


def get_theme_colors():
    """
    Get the current theme color palette.
    
    Returns:
        dict: Dictionary of color values
    """
    return {
        'bg': '#2b2b2b',
        'fg': '#ffffff',
        'select_bg': '#404040',
        'select_fg': '#ffffff',
        'entry_bg': '#404040',
        'button_bg': '#404040',
        'active_bg': '#505050',
        'accent': '#0078d4',
        'success': '#107c10',
        'warning': '#ff8c00',
        'error': '#d13438',
        'border': '#555555',
    }


def create_tooltip(widget, text):
    """
    Create a tooltip for a widget.
    
    Args:
        widget: The widget to attach the tooltip to
        text: The tooltip text
    """
    def show_tooltip(event):
        tooltip = tk.Toplevel()
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
        
        colors = get_theme_colors()
        tooltip.configure(bg=colors['select_bg'])
        
        label = tk.Label(tooltip, text=text,
                        background=colors['select_bg'],
                        foreground=colors['fg'],
                        font=('Segoe UI', 9),
                        padx=10, pady=5)
        label.pack()
        
        def hide_tooltip():
            tooltip.destroy()
        
        tooltip.after(3000, hide_tooltip)  # Auto-hide after 3 seconds
        widget.tooltip = tooltip
    
    def hide_tooltip(event):
        if hasattr(widget, 'tooltip'):
            widget.tooltip.destroy()
            delattr(widget, 'tooltip')
    
    widget.bind('<Enter>', show_tooltip)
    widget.bind('<Leave>', hide_tooltip)

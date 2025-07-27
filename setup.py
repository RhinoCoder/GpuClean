from setuptools import setup, find_packages

setup(
    name="gpu-memory-cleaner",
    version="1.0.0",
    description="A utility to clear NVIDIA GPU VRAM by terminating processes",
    author="RhinoCoder",
    author_email="abbilginn@hotmail.com",
    packages=find_packages(),
    py_modules=['gpu_cleaner'],
    entry_points={
        'console_scripts': [
            'gpu-clean=gpu_cleaner:main',
        ],
    },
    install_requires=[
        # No dependencies  
    ],
    python_requires='>=3.6',
    classifiers=[
        "Development Status :: 1 - Beta",
        "Intended Audience :: Developers,Scientists,Enthusiasts",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="gpu nvidia cuda memory vram cleanup",
    long_description="""
# GPU Memory Cleaner

A Python utility to clear NVIDIA GPU VRAM by terminating processes that are holding onto GPU memory.

## Features

- List all processes using GPU memory
- Terminate specific processes or all GPU processes
- Support for multiple GPUs
- Dry-run mode to preview actions
- Force termination option for stubborn processes
- Exclude specific processes from termination

## Usage

```bash
# Show GPU status and processes
gpu-clean --status

# Clear all GPU processes
gpu-clean --clear

# Force kill all GPU processes
gpu-clean --clear --force

# Clear processes on specific GPUs
gpu-clean --clear --gpu 0,1

# Exclude specific processes
gpu-clean --clear --exclude 1234,5678

# Dry run (preview what would be done)
gpu-clean --clear --dry-run
```

## Requirements

- NVIDIA GPU with drivers installed
- nvidia-smi command available
- Python 3.6+
""",
    long_description_content_type="text/markdown",
)
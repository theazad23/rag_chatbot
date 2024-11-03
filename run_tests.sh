#!/bin/bash

# Clean up previous test artifacts
echo "Cleaning up previous test artifacts..."
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type d -name ".pytest_cache" -exec rm -r {} +

# Set up test environment
echo "Setting up test environment..."
export PYTHONPATH="$PYTHONPATH:$(pwd)"

# Run the tests
echo "Running tests..."
pytest tests/ \
    -v \
    --tb=short \
    "$@"
exit_code=$?

# Clean up temporary files
echo "Cleaning up temporary files..."
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type d -name ".pytest_cache" -exec rm -r {} +

# Print result
if [ $exit_code -eq 0 ]; then
    echo "Tests completed successfully!"
else
    echo "Tests failed with exit code $exit_code"
fi

exit $exit_code
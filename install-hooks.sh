#!/bin/sh
# Run once after cloning to wire up the pre-commit hook.
cp .git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "Pre-commit hook installed."

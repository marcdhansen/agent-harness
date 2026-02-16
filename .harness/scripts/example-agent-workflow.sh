#!/bin/bash
# Example agent workflow using non-interactive mode (agent-6x9.6)

set -e

echo "🤖 Example Agent Workflow"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TASK_ID="${1:-agent-6x9.6}"
MODE="${2:-simple}"

echo "1. Initialize session (non-interactive)"
python check_protocol_compliance.py init \
  --mode "$MODE" \
  --issue-id "$TASK_ID"

echo ""
echo "2. Check status"
python check_protocol_compliance.py status

echo ""
echo "3. Do work (simulated)"
echo "   ... agent performs task ..."
sleep 1

echo ""
echo "4. Validate workspace"
bash .harness/scripts/validate-cleanup.sh || {
    echo "   Violations found, cleaning up..."
    bash .harness/scripts/auto-cleanup.sh <<< "y"
}

echo ""
echo "5. Close session"
python check_protocol_compliance.py close

echo ""
echo "✅ Agent workflow complete!"

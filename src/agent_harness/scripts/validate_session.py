import sys
from agent_harness.session_tracker import SessionTracker


def main():
    tracker = SessionTracker()
    if tracker.has_active_session():
        session = tracker.get_session()
        print(f"✅ Active session: {session['id']} (Issue: {session['issue_id']})")
        sys.exit(0)
    else:
        print("❌ No active harness session.")
        sys.exit(1)


if __name__ == "__main__":
    main()

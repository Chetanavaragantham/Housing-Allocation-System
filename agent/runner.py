import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import SessionLocal
from models.request import Request, RequestStatus
from agent.graph import housing_agent
from agent.state import HousingAgentState


def run_allocation_agent():
    """
    Main entry point for the housing allocation agent.
    Processes all pending requests in order — unresolved first, then by submitted_at.
    """
    db = SessionLocal()
    try:
        print("\n🏠 Housing Allocation Agent Starting...")
        print("=" * 50)

        # Load queue — unresolved first, then pending by submitted_at
        requests = (
            db.query(Request)
            .filter(
                Request.status.in_([
                    RequestStatus.pending,
                    RequestStatus.on_hold
                ])
            )
            .order_by(
                Request.status.desc(),     # on_hold first
                Request.submitted_at.asc() # then oldest first
            )
            .all()
        )

        if not requests:
            print("✅ No pending requests in queue.")
            return

        print(f"📋 Found {len(requests)} requests to process\n")

        results = {
            "allocated":  0,
            "on_hold":    0,
            "unresolved": 0,
            "rejected":   0
        }

        for request in requests:
            print(f"\n--- Processing Request #{request.id} ---")

            # Build initial state
            initial_state: HousingAgentState = {
                "request_id":          request.id,
                "request_type":        request.request_type.value,
                "student_id":          request.student_id,
                "student_profile":     {},
                "has_roommate_request": False,
                "roommate_ids":        [],
                "group_validated":     False,
                "available_rooms":     [],
                "room_id":             None,
                "compatibility_score": None,
                "attempts":            0,
                "current_node":        "start",
                "status":              "processing",
                "error_reason":        None,
                "notifications_sent":  []
            }

            # Run the agent
            try:
                final_state = housing_agent.invoke(initial_state)
                status = final_state["status"]

                if status in results:
                    results[status] += 1
                else:
                    results["rejected"] += 1

            except Exception as e:
                print(f"❌ Error processing request {request.id}: {e}")
                results["rejected"] += 1

        # Print summary
        print("\n" + "=" * 50)
        print("🏁 Agent Run Complete — Summary")
        print("=" * 50)
        print(f"  ✅ Allocated:  {results['allocated']}")
        print(f"  ⏸️  On Hold:    {results['on_hold']}")
        print(f"  🚨 Unresolved: {results['unresolved']}")
        print(f"  ❌ Rejected:   {results['rejected']}")
        print("=" * 50)

        return results

    finally:
        db.close()


if __name__ == "__main__":
    run_allocation_agent()
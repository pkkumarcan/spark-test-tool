import datetime
import random

# Mock experiments store
EXPERIMENTS = [
    {
        "experiment_id": "exp-801",
        "video_id": "dQw4w9WgXcQ",
        "name": "Thumbnail A/B Test - High Contrast vs Soft Gradient",
        "variants": {
            "A": {"ctr": 0.082, "impressions": 12000, "views": 984},
            "B": {"ctr": 0.051, "impressions": 11800, "views": 601}
        },
        "status": "completed",
        "winner": "A"
    }
]

async def get_kpi_dashboard():
    """Generates mock performance analytics data points for a channel view count dashboard."""
    # Generate past 7 days of metrics
    days = []
    base_views = 1500
    base_watch_time = 250
    base_subscribers = 45

    now = datetime.datetime.now()
    for i in range(7):
        day_date = (now - datetime.timedelta(days=6-i)).strftime("%Y-%m-%d")
        daily_views = base_views + random.randint(-300, 500)
        daily_wt = round(base_watch_time + random.uniform(-40, 80), 2)
        daily_subs = base_subscribers + random.randint(-10, 25)
        
        days.append({
            "date": day_date,
            "views": daily_views,
            "watch_time_hours": daily_wt,
            "subscribers_gained": daily_subs,
            "ctr_pct": round(random.uniform(4.5, 9.8), 2)
        })

    total_views = sum(d["views"] for d in days)
    total_wt = round(sum(d["watch_time_hours"] for d in days), 2)
    total_subs = sum(d["subscribers_gained"] for d in days)
    avg_ctr = round(sum(d["ctr_pct"] for d in days) / 7, 2)

    return {
        "summary": {
            "total_views": total_views,
            "total_watch_time_hours": total_wt,
            "total_subscribers_gained": total_subs,
            "average_ctr_pct": avg_ctr
        },
        "daily_data": days
    }

async def list_experiments():
    """Returns active and completed A/B optimization experiments."""
    return {"experiments": EXPERIMENTS}

async def create_experiment(video_id: str, name: str, var_a_name: str, var_b_name: str):
    """Register a new A/B thumbnail or title experiment."""
    new_exp = {
        "experiment_id": f"exp-{random.randint(802, 999)}",
        "video_id": video_id,
        "name": name,
        "variants": {
            "A": {"ctr": 0.0, "impressions": 0, "views": 0, "name": var_a_name},
            "B": {"ctr": 0.0, "impressions": 0, "views": 0, "name": var_b_name}
        },
        "status": "running",
        "winner": None
    }
    EXPERIMENTS.append(new_exp)
    return new_exp

import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from jira import JIRA, JIRAError
from typing import List, Dict, Optional
from datetime import datetime

app = FastAPI()

# --- Jira Configuration ---
JIRA_SERVER = os.environ.get("JIRA_SERVER")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")
JIRA_PROJECT = os.environ.get("JIRA_PROJECT")


def get_jira_client():
    """Initializes and returns a JIRA client instance."""
    try:
        options = {'server': JIRA_SERVER}
        jira = JIRA(options=options, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))
        return jira
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Jira: {e}")

# Response model
class WorkEstimate(BaseModel):
    issue_key: str
    summary: str
    original_estimate: str | None
    remaining_estimate: str | None

class WorkLogEntry(BaseModel):
    user: str
    hours: str

class WorkEffort(BaseModel):
    issue_key: str
    summary: str
    time_spent: Optional[str] = None
    worklogs: List[WorkLogEntry]

class FilteredIssue(BaseModel):
    issue_key: str
    summary: str
    priority: str
    severity: Optional[str]
    status: str

class DeliveryMetrics(BaseModel):
    total_issues: int
    completed_issues: int
    average_time_to_resolve: Optional[str]
    total_work_logged: Optional[str]
    

class JiraIssueResponse(BaseModel):
    issue_key: str
    summary: str | None
    description: str | None
    status: str | None
    priority: str | None
    reporter: str | None
    assignee: str | None
    issue_type: str | None
    created: str | None
    updated: str | None
    labels: list[str] | None
    components: list[str] | None
    project: str | None
    resolution: str | None
    resolutiondate: str | None
    timetracking_original: str | None
    timetracking_remaining: str | None
    
class SprintInsightsResponse(BaseModel):
    total_stories: int
    completed_stories: int
    pending_stories: int
    bugs_count: int
    velocity: float
    
@app.get("/jira/issues/work-estimates", response_model=List[WorkEstimate])
def get_work_estimates():
    
    jira = get_jira_client()
    
    try:
        jql_query = f"project = {JIRA_PROJECT}"
        issues = jira.search_issues(jql_query, maxResults=1000)

        results = []
        for issue in issues:
            timetracking = getattr(issue.fields, "timetracking", None)
            results.append(WorkEstimate(
                issue_key=issue.key,
                summary=issue.fields.summary,
                original_estimate=getattr(timetracking, "originalEstimate", None),
                remaining_estimate=getattr(timetracking, "remainingEstimate", None)
            ))
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve work estimates: {e}")

@app.get("/issues/assigned/{assignee_email}/{project_key}")
def get_assigned_issues(assignee_email: str, project_key: str):
    """
    Retrieves Jira issues assigned to a specific user (email or accountId) within a given project.
    """
    jira = get_jira_client()

    try:
        # Escape '@' character if necessary
        escaped_assignee = assignee_email.replace("@", "\\u0040")

        # Build JQL query (using equality operator instead of fuzzy search)
        jql_query = f'project = "{project_key}" AND assignee = "{escaped_assignee}" ORDER BY updated DESC'
        print(f"DEBUG - Executing JQL: {jql_query}")

        # Fetch issues
        issues = jira.search_issues(jql_query, maxResults=50)

        # Prepare clean response
        issues_list: List[Dict] = []
        for issue in issues:
            fields = issue.fields
            issues_list.append({
                "key": issue.key,
                "summary": fields.summary,
                "status": fields.status.name,
                "assignee": fields.assignee.displayName if fields.assignee else "Unassigned",
                "reporter": fields.reporter.displayName if fields.reporter else "Unknown",
                "created": fields.created,
                "updated": fields.updated,
            })

        return {"total_issues": len(issues_list), "issues": issues_list}

    except JIRAError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=f"Jira API Error: {e.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

@app.get("/jira/issues/work-efforts", response_model=List[WorkEffort])
def get_work_efforts():
    jira = get_jira_client()

    try:
        jql_query = f"project = {JIRA_PROJECT}"
        issues = jira.search_issues(jql_query, maxResults=100)

        results = []
        for issue in issues:
            issue_key = issue.key
            summary = issue.fields.summary

            # Fetch worklogs for the issue
            try:
                worklogs_data = jira.worklogs(issue_key)
                worklogs = []
                for wl in worklogs_data:
                    author = wl.author.displayName
                    time_spent = wl.timeSpent
                    worklogs.append(WorkLogEntry(user=author, hours=time_spent))
            except Exception as e:
                # Continue even if worklogs fail for one issue
                worklogs = []
                print(f"Warning: Failed to fetch worklogs for {issue_key}: {e}")

            # Optionally aggregate total time
            total_time = None
            if worklogs:
                total_time = ", ".join([wl.hours for wl in worklogs])

            results.append(WorkEffort(
                issue_key=issue_key,
                summary=summary,
                time_spent=total_time,
                worklogs=worklogs
            ))

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve work efforts: {e}")
        
@app.get("/jira/issues/filter", response_model=List[FilteredIssue])
def filter_by_criteria(
    priority: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """
    Retrieves Jira issues from JIRA project filtered by optional priority, severity, and status.
    """
    jira = get_jira_client()

    try:
        # Build JQL dynamically
        jql_parts = [f"project = {JIRA_PROJECT}"]
        if priority:
            jql_parts.append(f'priority = "{priority}"')
        if severity:
            jql_parts.append(f'severity = "{severity}"')
        if status:
            jql_parts.append(f'status = "{status}"')

        jql_query = " AND ".join(jql_parts)
        print(f"DEBUG - Executing JQL: {jql_query}")

        # Execute query
        issues = jira.search_issues(jql_query, maxResults=100)

        results = []
        for issue in issues:
            fields = issue.fields
            severity_value = getattr(fields, "severity", None)
            severity_name = getattr(severity_value, "name", "N/A") if severity_value else "N/A"

            results.append(FilteredIssue(
                issue_key=issue.key,
                summary=fields.summary,
                priority=fields.priority.name if fields.priority else "N/A",
                severity=severity_name,
                status=fields.status.name if fields.status else "N/A"
            ))

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to filter Jira issues: {e}")

@app.get("/jira/insights/delivery", response_model=DeliveryMetrics)
def get_delivery_metrics():
    """
    Computes delivery metrics for the Jira project.
    Metrics include:
    - Total issues
    - Completed (Done) issues
    - Average time to resolve (from created to resolved)
    - Total work logged (in hours)
    """
    jira = get_jira_client()

    try:
        jql_query = f"project = {JIRA_PROJECT}"
        issues = jira.search_issues(jql_query, maxResults=1000)

        total_issues = len(issues)
        completed_issues = 0
        total_resolve_time = 0
        resolved_count = 0
        total_work_logged_seconds = 0

        for issue in issues:
            fields = issue.fields

            # Count completed issues
            if fields.status.name.lower() == "done":
                completed_issues += 1

            # Calculate resolution time
            created_str = getattr(fields, "created", None)
            resolution_str = getattr(fields, "resolutiondate", None)
            if created_str and resolution_str:
                created_dt = datetime.strptime(created_str[:19], "%Y-%m-%dT%H:%M:%S")
                resolved_dt = datetime.strptime(resolution_str[:19], "%Y-%m-%dT%H:%M:%S")
                total_resolve_time += (resolved_dt - created_dt).total_seconds()
                resolved_count += 1

            # Sum worklogs (requires additional API call per issue)
            worklogs = jira.worklogs(issue.key)
            for wl in worklogs:
                total_work_logged_seconds += wl.timeSpentSeconds

        # Compute averages
        avg_time_to_resolve = (
            f"{round(total_resolve_time / resolved_count / 3600, 2)}h"
            if resolved_count > 0 else "0h"
        )
        total_work_logged = f"{round(total_work_logged_seconds / 3600, 2)}h"

        return DeliveryMetrics(
            total_issues=total_issues,
            completed_issues=completed_issues,
            average_time_to_resolve=avg_time_to_resolve,
            total_work_logged=total_work_logged,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute delivery metrics: {e}")

@app.get("/jira/issues/{issue_key}", response_model=JiraIssueResponse)
async def get_issue_details(issue_key: str):
    """
    Retrieves detailed Jira issue information using the working Jira client connection.
    """
    jira = get_jira_client()

    try:
        issue = jira.issue(issue_key)

        fields = issue.fields
        timetracking = getattr(fields, "timetracking", None)

        return JiraIssueResponse(
            issue_key=issue.key,
            summary=getattr(fields, "summary", None),
            description=getattr(fields, "description", None),
            status=getattr(fields.status, "name", None) if getattr(fields, "status", None) else None,
            priority=getattr(fields.priority, "name", None) if getattr(fields, "priority", None) else None,
            reporter=getattr(fields.reporter, "displayName", None) if getattr(fields, "reporter", None) else None,
            assignee=getattr(fields.assignee, "displayName", None) if getattr(fields, "assignee", None) else None,
            issue_type=getattr(fields.issuetype, "name", None) if getattr(fields, "issuetype", None) else None,
            created=getattr(fields, "created", None),
            updated=getattr(fields, "updated", None),
            labels=getattr(fields, "labels", []),
            components=[c.name for c in getattr(fields, "components", [])] if getattr(fields, "components", None) else [],
            project=getattr(fields.project, "name", None) if getattr(fields, "project", None) else None,
            resolution=getattr(fields.resolution, "name", None) if getattr(fields, "resolution", None) else None,
            resolutiondate=getattr(fields, "resolutiondate", None),
            timetracking_original=getattr(timetracking, "originalEstimate", None) if timetracking else None,
            timetracking_remaining=getattr(timetracking, "remainingEstimate", None) if timetracking else None,
        )

    except JIRAError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=f"Jira API Error: {e.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error retrieving issue {issue_key}: {e}")

@app.get("/jira/insights/sprint/currentsprint", response_model=SprintInsightsResponse)
def get_sprint_insights():
    """
    Retrieves sprint insights (assuming all issues in the project are part of the current sprint).
    """
    jira = get_jira_client()
    try:
        # You can adjust the project key here as needed
        jql_query = f"project = {JIRA_PROJECT}"
        issues = jira.search_issues(jql_query, maxResults=1000)

        total_stories = len(issues)
        completed_stories = 0
        pending_stories = 0
        bugs_count = 0
        total_story_points_completed = 0

        for issue in issues:
            fields = issue.fields

            # Determine issue type
            issue_type = getattr(fields.issuetype, "name", "").lower()

            # Count bugs separately
            if "bug" in issue_type:
                bugs_count += 1

            # Determine completion based on status
            status = getattr(fields.status, "name", "").lower()
            if "done" in status or "closed" in status or "resolved" in status:
                completed_stories += 1

            else:
                pending_stories += 1

        velocity = round((completed_stories / total_stories) * 100, 2) if total_stories > 0 else 0.0

        return SprintInsightsResponse(
            total_stories=total_stories,
            completed_stories=completed_stories,
            pending_stories=pending_stories,
            bugs_count=bugs_count,
            velocity=velocity
        )

    except JIRAError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=f"Jira API Error: {e.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate sprint insights: {e}")
       
if __name__ == "__main__":
    import uvicorn
    # Use the PORT environment variable provided by Code Engine
    port = int(os.environ.get("PORT", 8080))
    # Bind to 0.0.0.0 to be accessible from outside the container
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

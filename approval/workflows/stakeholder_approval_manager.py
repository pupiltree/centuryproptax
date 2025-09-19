"""Stakeholder approval workflow management system."""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid


class ApprovalStatus(Enum):
    """Approval workflow status."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    ESCALATED = "escalated"
    EXPIRED = "expired"


class StakeholderRole(Enum):
    """Stakeholder roles in approval process."""
    CEO = "ceo"
    CTO = "cto"
    CFO = "cfo"
    LEGAL_COUNSEL = "legal_counsel"
    COMPLIANCE_OFFICER = "compliance_officer"
    SECURITY_OFFICER = "security_officer"
    OPERATIONS_DIRECTOR = "operations_director"
    FINANCE_DIRECTOR = "finance_director"
    IT_DIRECTOR = "it_director"
    CUSTOMER_SERVICE_DIRECTOR = "customer_service_director"
    PROJECT_SPONSOR = "project_sponsor"
    BOARD_MEMBER = "board_member"


class ApprovalType(Enum):
    """Types of approvals required."""
    EXECUTIVE_APPROVAL = "executive_approval"
    FINANCIAL_APPROVAL = "financial_approval"
    TECHNICAL_APPROVAL = "technical_approval"
    SECURITY_APPROVAL = "security_approval"
    COMPLIANCE_APPROVAL = "compliance_approval"
    LEGAL_APPROVAL = "legal_approval"
    OPERATIONAL_APPROVAL = "operational_approval"
    BOARD_APPROVAL = "board_approval"
    GO_LIVE_APPROVAL = "go_live_approval"


@dataclass
class ApprovalRequirement:
    """Individual approval requirement."""
    requirement_id: str
    approval_type: ApprovalType
    required_stakeholders: List[StakeholderRole]
    minimum_approvals: int
    description: str
    documentation_required: List[str]
    deadline: datetime
    priority: str
    dependencies: List[str]


@dataclass
class StakeholderApproval:
    """Individual stakeholder approval record."""
    approval_id: str
    stakeholder_id: str
    stakeholder_role: StakeholderRole
    approval_type: ApprovalType
    status: ApprovalStatus
    submitted_timestamp: Optional[datetime]
    reviewed_timestamp: Optional[datetime]
    decision_timestamp: Optional[datetime]
    comments: str
    conditions: List[str]
    digital_signature: Optional[str]
    ip_address: Optional[str]


@dataclass
class ApprovalWorkflow:
    """Complete approval workflow."""
    workflow_id: str
    project_name: str
    project_description: str
    created_timestamp: datetime
    target_go_live_date: datetime
    workflow_status: ApprovalStatus
    approval_requirements: List[ApprovalRequirement]
    stakeholder_approvals: List[StakeholderApproval]
    overall_progress: float
    completed_requirements: List[str]
    pending_requirements: List[str]
    rejected_requirements: List[str]
    escalation_history: List[Dict[str, Any]]
    approval_summary: Dict[str, Any]


@dataclass
class StakeholderProfile:
    """Stakeholder profile and contact information."""
    stakeholder_id: str
    name: str
    role: StakeholderRole
    title: str
    department: str
    email: str
    phone: str
    approval_authority: List[ApprovalType]
    notification_preferences: Dict[str, bool]
    escalation_chain: List[str]
    delegate_id: Optional[str]


class StakeholderApprovalManager:
    """Comprehensive stakeholder approval workflow management."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.workflows: Dict[str, ApprovalWorkflow] = {}
        self.stakeholder_profiles: Dict[str, StakeholderProfile] = {}
        self._initialize_stakeholder_profiles()
        self._initialize_approval_requirements()

    def _initialize_stakeholder_profiles(self):
        """Initialize stakeholder profiles."""
        stakeholders = [
            StakeholderProfile(
                stakeholder_id="ceo_001",
                name="Executive Director",
                role=StakeholderRole.CEO,
                title="Chief Executive Officer",
                department="Executive",
                email="ceo@tdlr.texas.gov",
                phone="512-555-0001",
                approval_authority=[ApprovalType.EXECUTIVE_APPROVAL, ApprovalType.FINANCIAL_APPROVAL, ApprovalType.GO_LIVE_APPROVAL],
                notification_preferences={"email": True, "sms": True, "phone": False},
                escalation_chain=["board_001"],
                delegate_id=None
            ),
            StakeholderProfile(
                stakeholder_id="cto_001",
                name="Chief Technology Officer",
                role=StakeholderRole.CTO,
                title="Chief Technology Officer",
                department="Information Technology",
                email="cto@tdlr.texas.gov",
                phone="512-555-0002",
                approval_authority=[ApprovalType.TECHNICAL_APPROVAL, ApprovalType.SECURITY_APPROVAL],
                notification_preferences={"email": True, "sms": False, "phone": True},
                escalation_chain=["ceo_001"],
                delegate_id="it_dir_001"
            ),
            StakeholderProfile(
                stakeholder_id="cfo_001",
                name="Chief Financial Officer",
                role=StakeholderRole.CFO,
                title="Chief Financial Officer",
                department="Finance",
                email="cfo@tdlr.texas.gov",
                phone="512-555-0003",
                approval_authority=[ApprovalType.FINANCIAL_APPROVAL],
                notification_preferences={"email": True, "sms": True, "phone": False},
                escalation_chain=["ceo_001"],
                delegate_id="fin_dir_001"
            ),
            StakeholderProfile(
                stakeholder_id="legal_001",
                name="General Counsel",
                role=StakeholderRole.LEGAL_COUNSEL,
                title="General Counsel",
                department="Legal",
                email="legal@tdlr.texas.gov",
                phone="512-555-0004",
                approval_authority=[ApprovalType.LEGAL_APPROVAL, ApprovalType.COMPLIANCE_APPROVAL],
                notification_preferences={"email": True, "sms": False, "phone": True},
                escalation_chain=["ceo_001"],
                delegate_id=None
            ),
            StakeholderProfile(
                stakeholder_id="comp_001",
                name="Compliance Officer",
                role=StakeholderRole.COMPLIANCE_OFFICER,
                title="Chief Compliance Officer",
                department="Compliance",
                email="compliance@tdlr.texas.gov",
                phone="512-555-0005",
                approval_authority=[ApprovalType.COMPLIANCE_APPROVAL],
                notification_preferences={"email": True, "sms": True, "phone": False},
                escalation_chain=["legal_001", "ceo_001"],
                delegate_id=None
            ),
            StakeholderProfile(
                stakeholder_id="sec_001",
                name="Security Officer",
                role=StakeholderRole.SECURITY_OFFICER,
                title="Chief Information Security Officer",
                department="Information Security",
                email="security@tdlr.texas.gov",
                phone="512-555-0006",
                approval_authority=[ApprovalType.SECURITY_APPROVAL],
                notification_preferences={"email": True, "sms": True, "phone": True},
                escalation_chain=["cto_001", "ceo_001"],
                delegate_id=None
            ),
            StakeholderProfile(
                stakeholder_id="ops_001",
                name="Operations Director",
                role=StakeholderRole.OPERATIONS_DIRECTOR,
                title="Director of Operations",
                department="Operations",
                email="operations@tdlr.texas.gov",
                phone="512-555-0007",
                approval_authority=[ApprovalType.OPERATIONAL_APPROVAL],
                notification_preferences={"email": True, "sms": False, "phone": False},
                escalation_chain=["ceo_001"],
                delegate_id=None
            ),
            StakeholderProfile(
                stakeholder_id="cs_001",
                name="Customer Service Director",
                role=StakeholderRole.CUSTOMER_SERVICE_DIRECTOR,
                title="Director of Customer Service",
                department="Customer Service",
                email="customerservice@tdlr.texas.gov",
                phone="512-555-0008",
                approval_authority=[ApprovalType.OPERATIONAL_APPROVAL],
                notification_preferences={"email": True, "sms": True, "phone": False},
                escalation_chain=["ops_001", "ceo_001"],
                delegate_id=None
            )
        ]

        for stakeholder in stakeholders:
            self.stakeholder_profiles[stakeholder.stakeholder_id] = stakeholder

    def _initialize_approval_requirements(self):
        """Initialize standard approval requirements."""
        self.standard_requirements = [
            ApprovalRequirement(
                requirement_id="EXEC_001",
                approval_type=ApprovalType.EXECUTIVE_APPROVAL,
                required_stakeholders=[StakeholderRole.CEO],
                minimum_approvals=1,
                description="Executive approval for AI chatbot production deployment",
                documentation_required=["executive_summary", "business_case", "risk_assessment"],
                deadline=datetime.now() + timedelta(days=14),
                priority="Critical",
                dependencies=[]
            ),
            ApprovalRequirement(
                requirement_id="FIN_001",
                approval_type=ApprovalType.FINANCIAL_APPROVAL,
                required_stakeholders=[StakeholderRole.CFO],
                minimum_approvals=1,
                description="Financial approval for implementation and operational costs",
                documentation_required=["budget_breakdown", "roi_analysis", "cost_justification"],
                deadline=datetime.now() + timedelta(days=10),
                priority="Critical",
                dependencies=[]
            ),
            ApprovalRequirement(
                requirement_id="TECH_001",
                approval_type=ApprovalType.TECHNICAL_APPROVAL,
                required_stakeholders=[StakeholderRole.CTO, StakeholderRole.IT_DIRECTOR],
                minimum_approvals=1,
                description="Technical architecture and implementation approval",
                documentation_required=["technical_architecture", "performance_validation", "integration_plan"],
                deadline=datetime.now() + timedelta(days=7),
                priority="High",
                dependencies=[]
            ),
            ApprovalRequirement(
                requirement_id="SEC_001",
                approval_type=ApprovalType.SECURITY_APPROVAL,
                required_stakeholders=[StakeholderRole.SECURITY_OFFICER],
                minimum_approvals=1,
                description="Security and cybersecurity approval",
                documentation_required=["security_audit", "penetration_test_results", "vulnerability_assessment"],
                deadline=datetime.now() + timedelta(days=5),
                priority="Critical",
                dependencies=[]
            ),
            ApprovalRequirement(
                requirement_id="COMP_001",
                approval_type=ApprovalType.COMPLIANCE_APPROVAL,
                required_stakeholders=[StakeholderRole.COMPLIANCE_OFFICER, StakeholderRole.LEGAL_COUNSEL],
                minimum_approvals=2,
                description="TDLR regulatory compliance approval",
                documentation_required=["compliance_audit", "regulatory_mapping", "privacy_assessment"],
                deadline=datetime.now() + timedelta(days=7),
                priority="Critical",
                dependencies=[]
            ),
            ApprovalRequirement(
                requirement_id="LEGAL_001",
                approval_type=ApprovalType.LEGAL_APPROVAL,
                required_stakeholders=[StakeholderRole.LEGAL_COUNSEL],
                minimum_approvals=1,
                description="Legal review and approval",
                documentation_required=["legal_review", "contract_analysis", "liability_assessment"],
                deadline=datetime.now() + timedelta(days=10),
                priority="High",
                dependencies=[]
            ),
            ApprovalRequirement(
                requirement_id="OPS_001",
                approval_type=ApprovalType.OPERATIONAL_APPROVAL,
                required_stakeholders=[StakeholderRole.OPERATIONS_DIRECTOR, StakeholderRole.CUSTOMER_SERVICE_DIRECTOR],
                minimum_approvals=2,
                description="Operational readiness approval",
                documentation_required=["operational_procedures", "training_plan", "support_documentation"],
                deadline=datetime.now() + timedelta(days=14),
                priority="High",
                dependencies=["TECH_001", "SEC_001"]
            ),
            ApprovalRequirement(
                requirement_id="GOLIVE_001",
                approval_type=ApprovalType.GO_LIVE_APPROVAL,
                required_stakeholders=[StakeholderRole.CEO, StakeholderRole.CTO, StakeholderRole.COMPLIANCE_OFFICER],
                minimum_approvals=3,
                description="Final go-live approval for production deployment",
                documentation_required=["go_live_checklist", "rollback_plan", "monitoring_plan"],
                deadline=datetime.now() + timedelta(days=21),
                priority="Critical",
                dependencies=["EXEC_001", "FIN_001", "TECH_001", "SEC_001", "COMP_001", "LEGAL_001", "OPS_001"]
            )
        ]

    def create_approval_workflow(self, project_name: str, project_description: str,
                                target_go_live_date: datetime) -> str:
        """Create new approval workflow."""
        workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"

        workflow = ApprovalWorkflow(
            workflow_id=workflow_id,
            project_name=project_name,
            project_description=project_description,
            created_timestamp=datetime.now(),
            target_go_live_date=target_go_live_date,
            workflow_status=ApprovalStatus.PENDING,
            approval_requirements=self.standard_requirements.copy(),
            stakeholder_approvals=[],
            overall_progress=0.0,
            completed_requirements=[],
            pending_requirements=[req.requirement_id for req in self.standard_requirements],
            rejected_requirements=[],
            escalation_history=[],
            approval_summary={}
        )

        self.workflows[workflow_id] = workflow

        # Initialize stakeholder approval records
        for requirement in workflow.approval_requirements:
            for stakeholder_role in requirement.required_stakeholders:
                stakeholder = self._find_stakeholder_by_role(stakeholder_role)
                if stakeholder:
                    approval = StakeholderApproval(
                        approval_id=f"approval_{uuid.uuid4().hex[:8]}",
                        stakeholder_id=stakeholder.stakeholder_id,
                        stakeholder_role=stakeholder_role,
                        approval_type=requirement.approval_type,
                        status=ApprovalStatus.PENDING,
                        submitted_timestamp=None,
                        reviewed_timestamp=None,
                        decision_timestamp=None,
                        comments="",
                        conditions=[],
                        digital_signature=None,
                        ip_address=None
                    )
                    workflow.stakeholder_approvals.append(approval)

        self.logger.info(f"Created approval workflow {workflow_id} for {project_name}")
        return workflow_id

    def submit_stakeholder_approval(self, workflow_id: str, stakeholder_id: str,
                                  approval_type: ApprovalType, decision: ApprovalStatus,
                                  comments: str = "", conditions: List[str] = None,
                                  digital_signature: str = None, ip_address: str = None) -> bool:
        """Submit stakeholder approval decision."""
        if workflow_id not in self.workflows:
            self.logger.error(f"Workflow {workflow_id} not found")
            return False

        workflow = self.workflows[workflow_id]
        conditions = conditions or []

        # Find the approval record
        approval_record = None
        for approval in workflow.stakeholder_approvals:
            if (approval.stakeholder_id == stakeholder_id and
                approval.approval_type == approval_type and
                approval.status == ApprovalStatus.PENDING):
                approval_record = approval
                break

        if not approval_record:
            self.logger.error(f"Approval record not found for {stakeholder_id}, {approval_type.value}")
            return False

        # Update approval record
        approval_record.status = decision
        approval_record.submitted_timestamp = datetime.now()
        approval_record.decision_timestamp = datetime.now()
        approval_record.comments = comments
        approval_record.conditions = conditions
        approval_record.digital_signature = digital_signature
        approval_record.ip_address = ip_address

        # Update workflow status
        self._update_workflow_status(workflow_id)

        self.logger.info(f"Stakeholder approval submitted: {stakeholder_id} - {decision.value} for {approval_type.value}")
        return True

    def request_approval_review(self, workflow_id: str, stakeholder_id: str,
                              approval_type: ApprovalType) -> bool:
        """Request stakeholder to review and approve."""
        if workflow_id not in self.workflows:
            return False

        workflow = self.workflows[workflow_id]

        # Find approval record
        for approval in workflow.stakeholder_approvals:
            if (approval.stakeholder_id == stakeholder_id and
                approval.approval_type == approval_type):
                approval.status = ApprovalStatus.UNDER_REVIEW
                approval.reviewed_timestamp = datetime.now()

                # Send notification (simulated)
                self._send_approval_notification(stakeholder_id, workflow, approval)
                return True

        return False

    def escalate_approval(self, workflow_id: str, requirement_id: str, reason: str) -> bool:
        """Escalate approval to next level."""
        if workflow_id not in self.workflows:
            return False

        workflow = self.workflows[workflow_id]

        # Find requirement
        requirement = None
        for req in workflow.approval_requirements:
            if req.requirement_id == requirement_id:
                requirement = req
                break

        if not requirement:
            return False

        # Log escalation
        escalation = {
            "timestamp": datetime.now().isoformat(),
            "requirement_id": requirement_id,
            "reason": reason,
            "escalated_by": "system",
            "escalated_to": "next_level"
        }
        workflow.escalation_history.append(escalation)

        # Update requirement deadline
        requirement.deadline = requirement.deadline + timedelta(days=3)

        self.logger.warning(f"Escalated approval for requirement {requirement_id}: {reason}")
        return True

    def check_approval_deadlines(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Check for approaching or missed approval deadlines."""
        if workflow_id not in self.workflows:
            return []

        workflow = self.workflows[workflow_id]
        deadline_issues = []
        current_time = datetime.now()

        for requirement in workflow.approval_requirements:
            if requirement.requirement_id in workflow.completed_requirements:
                continue

            time_to_deadline = requirement.deadline - current_time
            days_remaining = time_to_deadline.days

            if days_remaining < 0:
                deadline_issues.append({
                    "requirement_id": requirement.requirement_id,
                    "issue": "expired",
                    "days_overdue": abs(days_remaining),
                    "priority": requirement.priority
                })
            elif days_remaining <= 2:
                deadline_issues.append({
                    "requirement_id": requirement.requirement_id,
                    "issue": "approaching",
                    "days_remaining": days_remaining,
                    "priority": requirement.priority
                })

        return deadline_issues

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive workflow status."""
        if workflow_id not in self.workflows:
            return None

        workflow = self.workflows[workflow_id]

        # Calculate progress
        total_requirements = len(workflow.approval_requirements)
        completed_requirements = len(workflow.completed_requirements)
        progress_percent = (completed_requirements / total_requirements * 100) if total_requirements > 0 else 0

        # Get approval summary by type
        approval_summary = {}
        for approval_type in ApprovalType:
            type_approvals = [a for a in workflow.stakeholder_approvals if a.approval_type == approval_type]
            if type_approvals:
                approved_count = len([a for a in type_approvals if a.status == ApprovalStatus.APPROVED])
                total_count = len(type_approvals)
                approval_summary[approval_type.value] = {
                    "approved": approved_count,
                    "total": total_count,
                    "status": "complete" if approved_count == total_count else "pending"
                }

        # Check for blockers
        blockers = []
        for requirement in workflow.approval_requirements:
            if requirement.requirement_id in workflow.rejected_requirements:
                blockers.append({
                    "type": "rejection",
                    "requirement": requirement.requirement_id,
                    "description": requirement.description
                })

        deadline_issues = self.check_approval_deadlines(workflow_id)
        blockers.extend([issue for issue in deadline_issues if issue["issue"] == "expired"])

        return {
            "workflow_id": workflow_id,
            "project_name": workflow.project_name,
            "overall_status": workflow.workflow_status.value,
            "progress_percent": progress_percent,
            "completed_requirements": workflow.completed_requirements,
            "pending_requirements": workflow.pending_requirements,
            "rejected_requirements": workflow.rejected_requirements,
            "approval_summary": approval_summary,
            "deadline_issues": deadline_issues,
            "blockers": blockers,
            "escalations": len(workflow.escalation_history),
            "target_go_live": workflow.target_go_live_date.isoformat(),
            "created": workflow.created_timestamp.isoformat()
        }

    def generate_approval_dashboard(self, workflow_id: str) -> Dict[str, Any]:
        """Generate approval dashboard for stakeholder visibility."""
        status = self.get_workflow_status(workflow_id)
        if not status:
            return {}

        workflow = self.workflows[workflow_id]

        # Stakeholder status
        stakeholder_status = {}
        for profile in self.stakeholder_profiles.values():
            stakeholder_approvals = [a for a in workflow.stakeholder_approvals if a.stakeholder_id == profile.stakeholder_id]
            pending_count = len([a for a in stakeholder_approvals if a.status == ApprovalStatus.PENDING])
            approved_count = len([a for a in stakeholder_approvals if a.status == ApprovalStatus.APPROVED])

            stakeholder_status[profile.stakeholder_id] = {
                "name": profile.name,
                "role": profile.role.value,
                "pending_approvals": pending_count,
                "completed_approvals": approved_count,
                "last_activity": max([a.decision_timestamp for a in stakeholder_approvals if a.decision_timestamp], default=None)
            }

        # Timeline view
        timeline = []
        for requirement in workflow.approval_requirements:
            timeline.append({
                "requirement_id": requirement.requirement_id,
                "description": requirement.description,
                "deadline": requirement.deadline.isoformat(),
                "status": "completed" if requirement.requirement_id in workflow.completed_requirements else "pending",
                "priority": requirement.priority,
                "dependencies": requirement.dependencies
            })

        return {
            "overview": status,
            "stakeholder_status": stakeholder_status,
            "timeline": sorted(timeline, key=lambda x: x["deadline"]),
            "next_actions": self._get_next_actions(workflow_id),
            "risk_indicators": self._get_risk_indicators(workflow_id)
        }

    def _update_workflow_status(self, workflow_id: str):
        """Update overall workflow status based on individual approvals."""
        workflow = self.workflows[workflow_id]

        # Check each requirement
        completed_requirements = []
        rejected_requirements = []

        for requirement in workflow.approval_requirements:
            requirement_approvals = [a for a in workflow.stakeholder_approvals
                                   if a.approval_type == requirement.approval_type]

            approved_count = len([a for a in requirement_approvals if a.status == ApprovalStatus.APPROVED])
            rejected_count = len([a for a in requirement_approvals if a.status == ApprovalStatus.REJECTED])

            if approved_count >= requirement.minimum_approvals:
                completed_requirements.append(requirement.requirement_id)
            elif rejected_count > 0:
                rejected_requirements.append(requirement.requirement_id)

        # Update workflow
        workflow.completed_requirements = completed_requirements
        workflow.rejected_requirements = rejected_requirements
        workflow.pending_requirements = [req.requirement_id for req in workflow.approval_requirements
                                       if req.requirement_id not in completed_requirements
                                       and req.requirement_id not in rejected_requirements]

        # Update overall progress
        total_requirements = len(workflow.approval_requirements)
        completed_count = len(completed_requirements)
        workflow.overall_progress = (completed_count / total_requirements * 100) if total_requirements > 0 else 0

        # Update overall workflow status
        if rejected_requirements:
            workflow.workflow_status = ApprovalStatus.REJECTED
        elif completed_count == total_requirements:
            workflow.workflow_status = ApprovalStatus.APPROVED
        elif completed_count > 0:
            workflow.workflow_status = ApprovalStatus.UNDER_REVIEW
        else:
            workflow.workflow_status = ApprovalStatus.PENDING

    def _find_stakeholder_by_role(self, role: StakeholderRole) -> Optional[StakeholderProfile]:
        """Find stakeholder by role."""
        for stakeholder in self.stakeholder_profiles.values():
            if stakeholder.role == role:
                return stakeholder
        return None

    def _send_approval_notification(self, stakeholder_id: str, workflow: ApprovalWorkflow,
                                  approval: StakeholderApproval):
        """Send approval notification to stakeholder."""
        stakeholder = self.stakeholder_profiles.get(stakeholder_id)
        if not stakeholder:
            return

        notification = {
            "timestamp": datetime.now().isoformat(),
            "stakeholder": stakeholder.name,
            "email": stakeholder.email,
            "project": workflow.project_name,
            "approval_type": approval.approval_type.value,
            "deadline": None,  # Would be set from requirement
            "message": f"Approval requested for {workflow.project_name}"
        }

        # Log notification (in production, would send actual email/SMS)
        self.logger.info(f"Notification sent to {stakeholder.name}: {notification['message']}")

    def _get_next_actions(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get next actions required for workflow progression."""
        workflow = self.workflows[workflow_id]
        next_actions = []

        # Find pending approvals with no dependencies
        for requirement in workflow.approval_requirements:
            if requirement.requirement_id in workflow.pending_requirements:
                dependencies_met = all(dep in workflow.completed_requirements
                                     for dep in requirement.dependencies)

                if dependencies_met:
                    next_actions.append({
                        "action": "request_approval",
                        "requirement_id": requirement.requirement_id,
                        "description": requirement.description,
                        "stakeholders": [role.value for role in requirement.required_stakeholders],
                        "deadline": requirement.deadline.isoformat(),
                        "priority": requirement.priority
                    })

        return sorted(next_actions, key=lambda x: x["deadline"])

    def _get_risk_indicators(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get risk indicators for workflow."""
        workflow = self.workflows[workflow_id]
        risks = []

        # Deadline risks
        deadline_issues = self.check_approval_deadlines(workflow_id)
        for issue in deadline_issues:
            if issue["issue"] == "expired":
                risks.append({
                    "type": "deadline_overdue",
                    "severity": "high",
                    "description": f"Requirement {issue['requirement_id']} is {issue['days_overdue']} days overdue"
                })
            elif issue["issue"] == "approaching":
                risks.append({
                    "type": "deadline_approaching",
                    "severity": "medium",
                    "description": f"Requirement {issue['requirement_id']} deadline in {issue['days_remaining']} days"
                })

        # Rejection risks
        if workflow.rejected_requirements:
            risks.append({
                "type": "approval_rejection",
                "severity": "critical",
                "description": f"{len(workflow.rejected_requirements)} requirements rejected"
            })

        # Go-live date risk
        days_to_golive = (workflow.target_go_live_date - datetime.now()).days
        if days_to_golive < 14 and workflow.overall_progress < 80:
            risks.append({
                "type": "golive_at_risk",
                "severity": "high",
                "description": f"Go-live in {days_to_golive} days but only {workflow.overall_progress:.1f}% approved"
            })

        return risks

    def export_approval_report(self, workflow_id: str) -> str:
        """Export comprehensive approval report."""
        dashboard = self.generate_approval_dashboard(workflow_id)
        return json.dumps(dashboard, default=str, indent=2)


# Example usage and testing
if __name__ == "__main__":
    approval_manager = StakeholderApprovalManager()

    print("Testing stakeholder approval workflow...")

    # Create workflow
    workflow_id = approval_manager.create_approval_workflow(
        "Century Property Tax AI Chatbot",
        "AI-powered customer support chatbot for property tax services",
        datetime.now() + timedelta(days=30)
    )

    print(f"Created workflow: {workflow_id}")

    # Submit some approvals
    approval_manager.submit_stakeholder_approval(
        workflow_id, "sec_001", ApprovalType.SECURITY_APPROVAL,
        ApprovalStatus.APPROVED, "Security review completed successfully"
    )

    approval_manager.submit_stakeholder_approval(
        workflow_id, "comp_001", ApprovalType.COMPLIANCE_APPROVAL,
        ApprovalStatus.APPROVED, "TDLR compliance validated"
    )

    approval_manager.submit_stakeholder_approval(
        workflow_id, "cto_001", ApprovalType.TECHNICAL_APPROVAL,
        ApprovalStatus.APPROVED, "Technical architecture approved"
    )

    # Get status
    status = approval_manager.get_workflow_status(workflow_id)
    print(f"\nWorkflow Status:")
    print(f"  Progress: {status['progress_percent']:.1f}%")
    print(f"  Completed: {len(status['completed_requirements'])}")
    print(f"  Pending: {len(status['pending_requirements'])}")
    print(f"  Overall Status: {status['overall_status']}")

    # Generate dashboard
    dashboard = approval_manager.generate_approval_dashboard(workflow_id)
    print(f"\nNext Actions: {len(dashboard['next_actions'])}")
    print(f"Risk Indicators: {len(dashboard['risk_indicators'])}")

    print(f"\nApproval Summary:")
    for approval_type, summary in status['approval_summary'].items():
        print(f"  {approval_type}: {summary['approved']}/{summary['total']} ({summary['status']})")

    print(f"\nStakeholder approval workflow system operational")
"""
Property Tax Message Templates for WhatsApp Business API.
Contains pre-approved templates and dynamic message generation for property tax workflows.
"""

import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime
from services.messaging.whatsapp_client import get_whatsapp_client
from src.core.logging import get_logger

logger = get_logger("property_tax_templates")


class PropertyTaxTemplates:
    """Property tax specific message templates for WhatsApp Business API."""

    def __init__(self):
        self.logger = logger
        self.whatsapp_client = get_whatsapp_client()

    # ===== PRE-APPROVED TEMPLATES =====
    # These would need to be submitted to WhatsApp for approval

    TEMPLATE_ASSESSMENT_NOTIFICATION = {
        "name": "property_assessment_notification",
        "language": "en_US",
        "category": "UTILITY",
        "components": [
            {
                "type": "HEADER",
                "format": "TEXT",
                "text": "Property Tax Assessment Notice"
            },
            {
                "type": "BODY",
                "text": "Hello {{1}}, your property at {{2}} has been assessed for tax year {{3}}. Assessment value: ${{4}}. Review details and appeal deadline: {{5}}."
            },
            {
                "type": "FOOTER",
                "text": "Century Property Tax Services"
            }
        ]
    }

    TEMPLATE_PAYMENT_REMINDER = {
        "name": "payment_reminder",
        "language": "en_US",
        "category": "UTILITY",
        "components": [
            {
                "type": "HEADER",
                "format": "TEXT",
                "text": "Property Tax Payment Reminder"
            },
            {
                "type": "BODY",
                "text": "Hi {{1}}, your property tax payment of ${{2}} for {{3}} is due on {{4}}. Pay online or visit our office to avoid penalties."
            },
            {
                "type": "FOOTER",
                "text": "Century Property Tax Services"
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {
                        "type": "URL",
                        "text": "Pay Online",
                        "url": "{{5}}"
                    },
                    {
                        "type": "PHONE_NUMBER",
                        "text": "Call Us",
                        "phone_number": "+1234567890"
                    }
                ]
            }
        ]
    }

    TEMPLATE_APPEAL_GUIDANCE = {
        "name": "appeal_guidance",
        "language": "en_US",
        "category": "MARKETING",
        "components": [
            {
                "type": "HEADER",
                "format": "TEXT",
                "text": "Property Tax Appeal Process"
            },
            {
                "type": "BODY",
                "text": "Hello {{1}}, you can appeal your property assessment of ${{2}}. Appeal deadline: {{3}}. Required documents: recent appraisal, comparable sales, property photos."
            },
            {
                "type": "FOOTER",
                "text": "We're here to help - Century Property Tax"
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {
                        "type": "QUICK_REPLY",
                        "text": "Start Appeal"
                    },
                    {
                        "type": "QUICK_REPLY",
                        "text": "Get Documents"
                    },
                    {
                        "type": "QUICK_REPLY",
                        "text": "Schedule Consultation"
                    }
                ]
            }
        ]
    }

    TEMPLATE_CONSULTATION_CONFIRMATION = {
        "name": "consultation_confirmation",
        "language": "en_US",
        "category": "UTILITY",
        "components": [
            {
                "type": "HEADER",
                "format": "TEXT",
                "text": "Consultation Scheduled"
            },
            {
                "type": "BODY",
                "text": "Hi {{1}}, your property tax consultation is confirmed for {{2}} at {{3}}. Topic: {{4}}. Our expert will contact you at this number."
            },
            {
                "type": "FOOTER",
                "text": "Century Property Tax Services"
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {
                        "type": "QUICK_REPLY",
                        "text": "Reschedule"
                    },
                    {
                        "type": "QUICK_REPLY",
                        "text": "Cancel"
                    }
                ]
            }
        ]
    }

    async def send_assessment_notification(self, to: str, property_owner: str,
                                         property_address: str, tax_year: str,
                                         assessment_value: str, appeal_deadline: str) -> Dict[str, Any]:
        """Send property assessment notification template."""
        try:
            components = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": property_owner},
                        {"type": "text", "text": property_address},
                        {"type": "text", "text": tax_year},
                        {"type": "text", "text": assessment_value},
                        {"type": "text", "text": appeal_deadline}
                    ]
                }
            ]

            result = await self.whatsapp_client.send_template_message(
                to=to,
                template_name="property_assessment_notification",
                components=components
            )

            self.logger.info(f"Assessment notification sent to {to[:5]}***",
                           success=result["success"], property_address=property_address)
            return result

        except Exception as e:
            self.logger.error(f"Failed to send assessment notification: {e}")
            return {"success": False, "error": str(e)}

    async def send_payment_reminder(self, to: str, property_owner: str,
                                  amount: str, property_address: str,
                                  due_date: str, payment_url: str) -> Dict[str, Any]:
        """Send payment reminder template with payment link."""
        try:
            components = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": property_owner},
                        {"type": "text", "text": amount},
                        {"type": "text", "text": property_address},
                        {"type": "text", "text": due_date},
                        {"type": "text", "text": payment_url}
                    ]
                }
            ]

            result = await self.whatsapp_client.send_template_message(
                to=to,
                template_name="payment_reminder",
                components=components
            )

            self.logger.info(f"Payment reminder sent to {to[:5]}***",
                           success=result["success"], amount=amount)
            return result

        except Exception as e:
            self.logger.error(f"Failed to send payment reminder: {e}")
            return {"success": False, "error": str(e)}

    async def send_appeal_guidance(self, to: str, property_owner: str,
                                 assessment_value: str, appeal_deadline: str) -> Dict[str, Any]:
        """Send appeal guidance template with quick actions."""
        try:
            components = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": property_owner},
                        {"type": "text", "text": assessment_value},
                        {"type": "text", "text": appeal_deadline}
                    ]
                }
            ]

            result = await self.whatsapp_client.send_template_message(
                to=to,
                template_name="appeal_guidance",
                components=components
            )

            self.logger.info(f"Appeal guidance sent to {to[:5]}***",
                           success=result["success"])
            return result

        except Exception as e:
            self.logger.error(f"Failed to send appeal guidance: {e}")
            return {"success": False, "error": str(e)}

    async def send_consultation_confirmation(self, to: str, client_name: str,
                                           date: str, time: str, topic: str) -> Dict[str, Any]:
        """Send consultation confirmation template."""
        try:
            components = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": client_name},
                        {"type": "text", "text": date},
                        {"type": "text", "text": time},
                        {"type": "text", "text": topic}
                    ]
                }
            ]

            result = await self.whatsapp_client.send_template_message(
                to=to,
                template_name="consultation_confirmation",
                components=components
            )

            self.logger.info(f"Consultation confirmation sent to {to[:5]}***",
                           success=result["success"], topic=topic)
            return result

        except Exception as e:
            self.logger.error(f"Failed to send consultation confirmation: {e}")
            return {"success": False, "error": str(e)}

    # ===== INTERACTIVE MESSAGES =====

    async def send_service_options_menu(self, to: str) -> Dict[str, Any]:
        """Send interactive list of property tax services."""
        try:
            interactive_data = {
                "header": {
                    "type": "text",
                    "text": "Property Tax Services"
                },
                "body": {
                    "text": "How can we help you with your property tax needs today? Please select a service:"
                },
                "footer": {
                    "text": "Century Property Tax Services"
                },
                "action": {
                    "button": "Select Service",
                    "sections": [
                        {
                            "title": "Assessment Services",
                            "rows": [
                                {
                                    "id": "assessment_review",
                                    "title": "Assessment Review",
                                    "description": "Review your property assessment"
                                },
                                {
                                    "id": "appeal_process",
                                    "title": "Appeal Process",
                                    "description": "File an assessment appeal"
                                }
                            ]
                        },
                        {
                            "title": "Payment Services",
                            "rows": [
                                {
                                    "id": "payment_info",
                                    "title": "Payment Information",
                                    "description": "Check payment due dates and amounts"
                                },
                                {
                                    "id": "payment_plans",
                                    "title": "Payment Plans",
                                    "description": "Set up installment plans"
                                }
                            ]
                        },
                        {
                            "title": "Consultation",
                            "rows": [
                                {
                                    "id": "schedule_consultation",
                                    "title": "Schedule Consultation",
                                    "description": "Book a consultation with our experts"
                                },
                                {
                                    "id": "document_review",
                                    "title": "Document Review",
                                    "description": "Review property tax documents"
                                }
                            ]
                        }
                    ]
                }
            }

            result = await self.whatsapp_client.send_interactive_message(
                to=to,
                interactive_type="list",
                interactive_data=interactive_data
            )

            self.logger.info(f"Service options menu sent to {to[:5]}***",
                           success=result["success"])
            return result

        except Exception as e:
            self.logger.error(f"Failed to send service options menu: {e}")
            return {"success": False, "error": str(e)}

    async def send_quick_actions_buttons(self, to: str, context: str = "general") -> Dict[str, Any]:
        """Send quick action buttons based on context."""
        try:
            if context == "assessment":
                header_text = "Assessment Actions"
                body_text = "What would you like to do with your property assessment?"
                buttons = [
                    {"type": "reply", "reply": {"id": "view_assessment", "title": "View Assessment"}},
                    {"type": "reply", "reply": {"id": "file_appeal", "title": "File Appeal"}},
                    {"type": "reply", "reply": {"id": "schedule_review", "title": "Schedule Review"}}
                ]
            elif context == "payment":
                header_text = "Payment Options"
                body_text = "Choose your payment option:"
                buttons = [
                    {"type": "reply", "reply": {"id": "pay_now", "title": "Pay Now"}},
                    {"type": "reply", "reply": {"id": "payment_plan", "title": "Payment Plan"}},
                    {"type": "reply", "reply": {"id": "payment_info", "title": "Payment Info"}}
                ]
            else:
                header_text = "Quick Actions"
                body_text = "What can we help you with today?"
                buttons = [
                    {"type": "reply", "reply": {"id": "check_assessment", "title": "Check Assessment"}},
                    {"type": "reply", "reply": {"id": "payment_status", "title": "Payment Status"}},
                    {"type": "reply", "reply": {"id": "talk_to_expert", "title": "Talk to Expert"}}
                ]

            interactive_data = {
                "header": {
                    "type": "text",
                    "text": header_text
                },
                "body": {
                    "text": body_text
                },
                "footer": {
                    "text": "Century Property Tax Services"
                },
                "action": {
                    "buttons": buttons
                }
            }

            result = await self.whatsapp_client.send_interactive_message(
                to=to,
                interactive_type="button",
                interactive_data=interactive_data
            )

            self.logger.info(f"Quick actions buttons sent to {to[:5]}***",
                           success=result["success"], context=context)
            return result

        except Exception as e:
            self.logger.error(f"Failed to send quick actions buttons: {e}")
            return {"success": False, "error": str(e)}

    # ===== DYNAMIC MESSAGES =====

    async def send_property_lookup_result(self, to: str, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send property lookup results with formatted data."""
        try:
            if not property_data:
                message = """🏠 **Property Search Results**

No property found with the provided information. Please check:
• Property address spelling
• Parcel number format
• Owner name spelling

Would you like to try another search or speak with an expert?"""
            else:
                address = property_data.get("address", "Address not available")
                owner = property_data.get("owner", "Owner not available")
                assessed_value = property_data.get("assessed_value", "N/A")
                tax_year = property_data.get("tax_year", "N/A")
                due_amount = property_data.get("due_amount", "N/A")
                due_date = property_data.get("due_date", "N/A")

                message = f"""🏠 **Property Tax Information**

**Property:** {address}
**Owner:** {owner}
**Tax Year:** {tax_year}
**Assessed Value:** ${assessed_value:,} if assessed_value != "N/A" else assessed_value
**Amount Due:** ${due_amount} if due_amount != "N/A" else due_amount
**Due Date:** {due_date}

How can we help you with this property?"""

            result = await self.whatsapp_client.send_text_message(to, message)

            # Follow up with quick actions if property found
            if property_data:
                await self.send_quick_actions_buttons(to, "general")

            self.logger.info(f"Property lookup result sent to {to[:5]}***",
                           success=result["success"], property_found=bool(property_data))
            return result

        except Exception as e:
            self.logger.error(f"Failed to send property lookup result: {e}")
            return {"success": False, "error": str(e)}

    async def send_appeal_document_checklist(self, to: str) -> Dict[str, Any]:
        """Send appeal document checklist."""
        try:
            message = """📋 **Property Tax Appeal Document Checklist**

To file a successful appeal, please gather:

**Required Documents:**
✅ Recent professional appraisal (within 12 months)
✅ Comparable property sales (3-5 recent sales)
✅ Property photos (exterior and any damage)
✅ Repair estimates (if applicable)

**Optional Supporting Documents:**
• Income and expense statements (for income properties)
• Environmental reports
• Survey documents
• Previous year's assessment notices

**Important Deadlines:**
• Appeal filing: Within 60 days of assessment notice
• Document submission: Within 30 days of appeal filing

Would you like help gathering any of these documents or filing your appeal?"""

            result = await self.whatsapp_client.send_text_message(to, message)

            # Follow up with appeal-specific actions
            await self.send_quick_actions_buttons(to, "assessment")

            self.logger.info(f"Appeal document checklist sent to {to[:5]}***",
                           success=result["success"])
            return result

        except Exception as e:
            self.logger.error(f"Failed to send appeal checklist: {e}")
            return {"success": False, "error": str(e)}

    async def send_payment_options(self, to: str, amount: str, due_date: str) -> Dict[str, Any]:
        """Send payment options with amount and due date."""
        try:
            message = f"""💳 **Property Tax Payment Options**

**Amount Due:** ${amount}
**Due Date:** {due_date}

**Payment Methods:**
🌐 **Online Payment** - Pay instantly with credit/debit card
🏦 **Bank Transfer** - ACH transfer from your bank account
🏢 **In Person** - Visit our office with cash, check, or card
📧 **Mail** - Send check to our mailing address

**Payment Plans Available:**
• Monthly installments
• Quarterly payments
• Senior citizen discounts

**Late Payment Penalties:**
• 1.5% per month after due date
• Additional fees may apply

Choose your preferred payment method:"""

            result = await self.whatsapp_client.send_text_message(to, message)

            # Follow up with payment action buttons
            await self.send_quick_actions_buttons(to, "payment")

            self.logger.info(f"Payment options sent to {to[:5]}***",
                           success=result["success"], amount=amount)
            return result

        except Exception as e:
            self.logger.error(f"Failed to send payment options: {e}")
            return {"success": False, "error": str(e)}

    def get_template_list(self) -> List[Dict[str, Any]]:
        """Get list of all available templates for WhatsApp submission."""
        return [
            self.TEMPLATE_ASSESSMENT_NOTIFICATION,
            self.TEMPLATE_PAYMENT_REMINDER,
            self.TEMPLATE_APPEAL_GUIDANCE,
            self.TEMPLATE_CONSULTATION_CONFIRMATION
        ]


# Global instance
_property_tax_templates = None

def get_property_tax_templates() -> PropertyTaxTemplates:
    """Get global property tax templates instance."""
    global _property_tax_templates
    if _property_tax_templates is None:
        _property_tax_templates = PropertyTaxTemplates()
    return _property_tax_templates
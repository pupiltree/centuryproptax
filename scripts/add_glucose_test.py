#!/usr/bin/env python3
"""
Add GLUCOSE test to database for production deployment.
This script ensures the Fasting Blood Sugar test is available for order creation.
"""

import asyncio
import sys
import os
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
sys.path.append('.')

async def add_glucose_test_to_production():
    """Add GLUCOSE test to database if it doesn't exist."""
    
    try:
        print("➕ Ensuring GLUCOSE test exists in database...")
        
        from services.persistence.database import get_database_manager, TestCatalog
        
        db_manager = await get_database_manager()
        
        async with db_manager.get_session() as session:
            from sqlalchemy import select
            
            # Check if GLUCOSE test already exists
            existing = await session.execute(
                select(TestCatalog).where(TestCatalog.test_code == 'GLUCOSE')
            )
            
            if existing.first():
                print('✅ GLUCOSE test already exists')
                return True
                
            # Add GLUCOSE test
            glucose_test = TestCatalog(
                test_code='GLUCOSE',
                name='Fasting Blood Sugar',
                category='Diabetes',
                description='Blood glucose level after overnight fast - primary screening test for diabetes',
                includes=['Glucose level measurement', 'Diabetes screening', 'Pre-diabetes detection'],
                sample_type='Blood',
                fasting_required=True,
                price=Decimal('150.00'),
                discounted_price=Decimal('150.00'),
                available=True,
                home_collection=True,
                lab_visit_required=False,
                conditions_recommended_for=['diabetes', 'prediabetes', 'screening', 'first_time_diabetes_check'],
                age_group='All',
                gender_specific=None
            )
            
            session.add(glucose_test)
            await session.commit()
            
            print('✅ Added GLUCOSE test: Fasting Blood Sugar (₹150)')
            
            # Verify addition
            result = await session.execute(
                select(TestCatalog.test_code, TestCatalog.name, TestCatalog.price, TestCatalog.available)
                .where(TestCatalog.test_code == 'GLUCOSE')
            )
            
            test = result.first()
            if test:
                print(f'✅ Verified: {test.test_code} - {test.name} (₹{test.price}) Available: {test.available}')
                return True
            else:
                print('❌ Failed to verify GLUCOSE test addition')
                return False
            
    except Exception as e:
        print(f"❌ Error adding GLUCOSE test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(add_glucose_test_to_production())
    print(f"\n🏁 GLUCOSE test setup: {'✅ SUCCESS' if success else '❌ FAILED'}")
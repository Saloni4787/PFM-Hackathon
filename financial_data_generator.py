"""
Financial Data Generator

This script generates synthetic financial data for the Personal Finance Manager application.
It creates a coherent set of user profiles, transactions, goals, budgets, subscriptions,
and asset allocations for demonstration purposes.

This version is specifically formatted to be compatible with the Transaction Analysis Agent.
"""

import os
import csv
import random
import datetime
from typing import Dict, List, Any, Tuple
import pandas as pd
from dateutil.relativedelta import relativedelta

# Set random seed for reproducibility
random.seed(42)

# Constants
NUM_USERS = 10
BASE_DATA_PATH = "./synthetic_data"
CURRENT_DATE = datetime.datetime(2025, 3, 15)  # March 15, 2025

# Global counters for IDs
global_goal_counter = 0
global_budget_counter = 0
global_subscription_counter = 0
global_transaction_counter = 0

# User archetypes for coherent narratives
USER_ARCHETYPES = [
    {
        "name": "Young Professional",
        "age_range": (25, 35),
        "income_range": (60000, 90000),
        "risk_profile": "High",
        "risk_category": "Growth",
        "employment": "Employed",
        "goals": ["Home Purchase", "Travel", "Emergency Fund"],
        "main_goal": "Home Purchase",
        "marital_status": "Single",
        "savings_ratio": (0.2, 0.4),
        "checking_ratio": (0.1, 0.15),
        "language": "English",
        "budget_categories": ["Rent", "Dining", "Entertainment", "Transportation", "Shopping"]
    },
    {
        "name": "Parent",
        "age_range": (35, 45),
        "income_range": (80000, 120000),
        "risk_profile": "Medium",
        "risk_category": "Balanced",
        "employment": "Employed",
        "goals": ["Education", "Home Purchase", "Retirement"],
        "main_goal": "Education",
        "marital_status": "Married",
        "savings_ratio": (0.3, 0.5),
        "checking_ratio": (0.1, 0.2),
        "language": "English",
        "budget_categories": ["Mortgage", "Groceries", "Childcare", "Healthcare", "Utilities"]
    },
    {
        "name": "Pre-Retiree",
        "age_range": (55, 65),
        "income_range": (90000, 150000),
        "risk_profile": "Medium",
        "risk_category": "Conservative",
        "employment": "Employed",
        "goals": ["Retirement", "Travel", "Medical Expenses"],
        "main_goal": "Retirement",
        "marital_status": "Married",
        "savings_ratio": (0.6, 1.0),
        "checking_ratio": (0.1, 0.2),
        "language": "English",
        "budget_categories": ["Mortgage", "Healthcare", "Insurance", "Utilities", "Travel"]
    },
    {
        "name": "Risk-Averse Saver",
        "age_range": (30, 50),
        "income_range": (50000, 80000),
        "risk_profile": "Low",
        "risk_category": "Conservative",
        "employment": "Employed",
        "goals": ["Emergency Fund", "Medical Expenses", "Home Purchase"],
        "main_goal": "Emergency Fund",
        "marital_status": "Single",
        "savings_ratio": (0.4, 0.6),
        "checking_ratio": (0.2, 0.3),
        "language": "Spanish",
        "budget_categories": ["Rent", "Groceries", "Utilities", "Healthcare", "Savings"]
    },
    {
        "name": "Entrepreneur",
        "age_range": (30, 45),
        "income_range": (80000, 200000),
        "risk_profile": "High",
        "risk_category": "Aggressive",
        "employment": "Self-Employed",
        "goals": ["Starting Business", "Retirement", "Home Purchase"],
        "main_goal": "Starting Business",
        "marital_status": "Single",
        "savings_ratio": (0.5, 0.8),
        "checking_ratio": (0.2, 0.4),
        "language": "English",
        "budget_categories": ["Office Rent", "Equipment", "Marketing", "Travel", "Legal Services"]
    },
    {
        "name": "High-Income Investor",
        "age_range": (35, 55),
        "income_range": (150000, 300000),
        "risk_profile": "High",
        "risk_category": "Aggressive",
        "employment": "Employed",
        "goals": ["Retirement", "Real Estate Investment", "Education"],
        "main_goal": "Retirement",
        "marital_status": "Married",
        "savings_ratio": (0.8, 1.5),
        "checking_ratio": (0.2, 0.3),
        "language": "English",
        "budget_categories": ["Mortgage", "Investments", "Travel", "Dining", "Shopping"]
    },
    {
        "name": "Budget-Conscious",
        "age_range": (25, 40),
        "income_range": (40000, 65000),
        "risk_profile": "Low",
        "risk_category": "Risk Averse",
        "employment": "Employed",
        "goals": ["Debt Repayment", "Emergency Fund", "Car Purchase"],
        "main_goal": "Debt Repayment",
        "marital_status": "Single",
        "savings_ratio": (0.1, 0.3),
        "checking_ratio": (0.05, 0.15),
        "language": "English",
        "budget_categories": ["Rent", "Groceries", "Debt Payments", "Transportation", "Utilities"]
    },
    {
        "name": "Newlywed Couple",
        "age_range": (25, 35),
        "income_range": (70000, 110000),
        "risk_profile": "Medium",
        "risk_category": "Balanced",
        "employment": "Employed",
        "goals": ["Home Purchase", "Wedding", "Travel"],
        "main_goal": "Wedding",
        "marital_status": "Married",
        "savings_ratio": (0.3, 0.5),
        "checking_ratio": (0.1, 0.2),
        "language": "Spanish",
        "budget_categories": ["Rent", "Wedding Expenses", "Dining", "Travel", "Shopping"]
    },
    {
        "name": "Mid-Career Professional",
        "age_range": (35, 50),
        "income_range": (80000, 130000),
        "risk_profile": "Medium",
        "risk_category": "Growth",
        "employment": "Employed",
        "goals": ["Home Purchase", "Education", "Retirement", "Travel"],
        "main_goal": "Education",
        "marital_status": "Married",
        "savings_ratio": (0.4, 0.7),
        "checking_ratio": (0.1, 0.2),
        "language": "English",
        "budget_categories": ["Mortgage", "Education", "Groceries", "Childcare", "Entertainment"]
    },
    {
        "name": "Recent Graduate",
        "age_range": (22, 28),
        "income_range": (35000, 60000),
        "risk_profile": "Medium",
        "risk_category": "Growth",
        "employment": "Employed",
        "goals": ["Debt Repayment", "Emergency Fund", "Car Purchase"],
        "main_goal": "Debt Repayment",
        "marital_status": "Single",
        "savings_ratio": (0.05, 0.2),
        "checking_ratio": (0.05, 0.1),
        "language": "English",
        "budget_categories": ["Rent", "Student Loans", "Groceries", "Transportation", "Entertainment"]
    }
]

# Investment profiles
INVESTMENT_PROFILES = {
    "Risk Averse": {
        "Cash": (50, 70),
        "Bonds": (20, 40),
        "Large Cap": (5, 10),
        "Mid Cap": (0, 0),
        "Small Cap": (0, 0),
        "International": (0, 5),
        "Real Estate": (0, 0),
        "Commodities": (0, 0)
    },
    "Conservative": {
        "Cash": (30, 50),
        "Bonds": (30, 50),
        "Large Cap": (10, 20),
        "Mid Cap": (0, 5),
        "Small Cap": (0, 0),
        "International": (5, 10),
        "Real Estate": (0, 5),
        "Commodities": (0, 0)
    },
    "Balanced": {
        "Cash": (15, 30),
        "Bonds": (25, 40),
        "Large Cap": (20, 30),
        "Mid Cap": (5, 10),
        "Small Cap": (0, 5),
        "International": (5, 15),
        "Real Estate": (0, 10),
        "Commodities": (0, 5)
    },
    "Growth": {
        "Cash": (5, 15),
        "Bonds": (10, 25),
        "Large Cap": (25, 40),
        "Mid Cap": (10, 20),
        "Small Cap": (5, 15),
        "International": (10, 20),
        "Real Estate": (0, 10),
        "Commodities": (0, 5)
    },
    "Aggressive": {
        "Cash": (0, 10),
        "Bonds": (0, 15),
        "Large Cap": (25, 40),
        "Mid Cap": (15, 25),
        "Small Cap": (10, 20),
        "International": (15, 25),
        "Real Estate": (0, 10),
        "Commodities": (0, 10)
    }
}

# Goal templates
GOAL_TEMPLATES = {
    "Emergency Fund": {
        "timeline_range": (3, 12),  # months
        "amount_factor": (3, 6),  # months of expenses
        "priority": "Very High",
        "timeline_type": "Short-term"
    },
    "Home Purchase": {
        "timeline_range": (12, 60),
        "amount_factor": (0.1, 0.2),  # percentage of home value (down payment)
        "home_value_factor": (3, 5),  # multiple of annual income
        "priority": "High",
        "timeline_type": "Long-term"
    },
    "Retirement": {
        "timeline_range": (60, 360),
        "amount_factor": (10, 20),  # multiple of annual income
        "priority": "High",
        "timeline_type": "Long-term"
    },
    "Education": {
        "timeline_range": (24, 120),
        "amount_fixed_range": (50000, 200000),
        "priority": "Medium",
        "timeline_type": "Medium-term"
    },
    "Travel": {
        "timeline_range": (3, 18),
        "amount_fixed_range": (2000, 15000),
        "priority": "Low",
        "timeline_type": "Short-term"
    },
    "Wedding": {
        "timeline_range": (6, 24),
        "amount_fixed_range": (15000, 50000),
        "priority": "Medium",
        "timeline_type": "Medium-term"
    },
    "Car Purchase": {
        "timeline_range": (6, 36),
        "amount_fixed_range": (15000, 60000),
        "priority": "Medium",
        "timeline_type": "Medium-term"
    },
    "Starting Business": {
        "timeline_range": (12, 48),
        "amount_fixed_range": (50000, 200000),
        "priority": "High",
        "timeline_type": "Long-term"
    },
    "Debt Repayment": {
        "timeline_range": (12, 60),
        "amount_fixed_range": (10000, 100000),
        "priority": "Very High",
        "timeline_type": "Medium-term"
    },
    "Medical Expenses": {
        "timeline_range": (3, 24),
        "amount_fixed_range": (5000, 30000),
        "priority": "High",
        "timeline_type": "Short-term"
    },
    "Real Estate Investment": {
        "timeline_range": (24, 60),
        "amount_fixed_range": (50000, 300000),
        "priority": "Medium",
        "timeline_type": "Long-term"
    }
}

# Budget categories
BUDGET_CATEGORIES = {
    "Rent": (0.25, 0.35),  # percentage of monthly income
    "Mortgage": (0.25, 0.35),
    "Groceries": (0.1, 0.15),
    "Dining": (0.05, 0.1),
    "Entertainment": (0.03, 0.08),
    "Transportation": (0.05, 0.1),
    "Shopping": (0.05, 0.1),
    "Utilities": (0.05, 0.08),
    "Healthcare": (0.05, 0.1),
    "Insurance": (0.05, 0.08),
    "Childcare": (0.1, 0.2),
    "Education": (0.1, 0.2),
    "Travel": (0.05, 0.1),
    "Savings": (0.1, 0.2),
    "Debt Payments": (0.1, 0.3),
    "Student Loans": (0.1, 0.2),
    "Office Rent": (0.1, 0.15),
    "Equipment": (0.05, 0.1),
    "Marketing": (0.05, 0.1),
    "Legal Services": (0.02, 0.05),
    "Investments": (0.1, 0.2),
    "Wedding Expenses": (0.1, 0.2)
}

# Transaction types
TRANSACTION_TYPES = ["Purchase", "Transfer", "Withdrawal", "Deposit", "Payment", "Refund"]

# Subscription services
SUBSCRIPTION_SERVICES = [
    {"name": "Netflix", "amount_range": (15, 20), "frequency": "Monthly"},
    {"name": "Spotify", "amount_range": (10, 15), "frequency": "Monthly"},
    {"name": "Amazon Prime", "amount_range": (12, 15), "frequency": "Monthly"},
    {"name": "Apple Music", "amount_range": (10, 15), "frequency": "Monthly"},
    {"name": "Disney+", "amount_range": (8, 12), "frequency": "Monthly"},
    {"name": "HBO Max", "amount_range": (15, 18), "frequency": "Monthly"},
    {"name": "Hulu", "amount_range": (12, 15), "frequency": "Monthly"},
    {"name": "Adobe Creative Cloud", "amount_range": (20, 60), "frequency": "Monthly"},
    {"name": "Microsoft 365", "amount_range": (7, 10), "frequency": "Monthly"},
    {"name": "Gym Membership", "amount_range": (30, 80), "frequency": "Monthly"},
    {"name": "New York Times", "amount_range": (5, 10), "frequency": "Monthly"},
    {"name": "Audible", "amount_range": (15, 20), "frequency": "Monthly"},
    {"name": "YouTube Premium", "amount_range": (12, 18), "frequency": "Monthly"},
    {"name": "PlayStation Plus", "amount_range": (10, 15), "frequency": "Monthly"},
    {"name": "Xbox Game Pass", "amount_range": (10, 15), "frequency": "Monthly"},
    {"name": "iCloud Storage", "amount_range": (3, 10), "frequency": "Monthly"},
    {"name": "Google Drive Storage", "amount_range": (2, 10), "frequency": "Monthly"},
    {"name": "Zoom Pro", "amount_range": (15, 20), "frequency": "Monthly"},
    {"name": "Canva Pro", "amount_range": (12, 15), "frequency": "Monthly"},
    {"name": "HelloFresh", "amount_range": (60, 120), "frequency": "Weekly"},
    {"name": "Blue Apron", "amount_range": (60, 120), "frequency": "Weekly"},
    {"name": "BarkBox", "amount_range": (20, 35), "frequency": "Monthly"},
    {"name": "Dollar Shave Club", "amount_range": (5, 15), "frequency": "Monthly"},
    {"name": "Stitch Fix", "amount_range": (20, 50), "frequency": "Monthly"},
    {"name": "Peloton", "amount_range": (40, 50), "frequency": "Monthly"},
    {"name": "Identity Theft Protection", "amount_range": (10, 30), "frequency": "Monthly"},
    {"name": "LinkedIn Premium", "amount_range": (30, 50), "frequency": "Monthly"},
    {"name": "Domain Hosting", "amount_range": (10, 30), "frequency": "Monthly"},
    {"name": "VPN Service", "amount_range": (5, 15), "frequency": "Monthly"},
    {"name": "Language Learning App", "amount_range": (10, 20), "frequency": "Monthly"}
]

# Merchant categories and examples
MERCHANT_CATEGORIES = {
    "Groceries": ["Whole Foods", "Trader Joe's", "Safeway", "Kroger", "Albertsons", "Costco", "Walmart", "Target"],
    "Dining": ["McDonald's", "Starbucks", "Chipotle", "Subway", "Local Restaurant", "Panera Bread", "Applebee's", "Chili's"],
    "Shopping": ["Amazon", "Target", "Walmart", "Best Buy", "Macy's", "Nordstrom", "H&M", "Zara", "IKEA"],
    "Entertainment": ["Netflix", "AMC Theaters", "Hulu", "Spotify", "Disney+", "HBO Max", "Apple TV+", "Concert Tickets"],
    "Transportation": ["Uber", "Lyft", "Gas Station", "Public Transit", "Airline Tickets", "Car Rental", "Car Service"],
    "Utilities": ["Electric Company", "Water Service", "Gas Company", "Internet Provider", "Phone Provider", "Cable Company"],
    "Healthcare": ["Pharmacy", "Doctor's Office", "Hospital", "Dental Office", "Vision Center", "Health Insurance"],
    "Insurance": ["Car Insurance", "Home Insurance", "Life Insurance", "Dental Insurance", "Vision Insurance"],
    "Education": ["Tuition Payment", "Textbooks", "School Supplies", "Online Course", "Educational Software"],
    "Housing": ["Rent Payment", "Mortgage Payment", "Home Repair", "Furniture Store", "Home Depot", "Lowe's"],
    "Travel": ["Hotel", "Airline", "Car Rental", "Cruise Line", "Travel Agency", "Vacation Rental", "Travel Insurance"],
    "Professional Services": ["Lawyer", "Accountant", "Financial Advisor", "Consultant", "Tax Service"],
    "Business Expenses": ["Office Supplies", "Software Subscription", "Business Travel", "Coworking Space", "Marketing Service"],
    "Childcare": ["Daycare", "Babysitter", "Nanny Service", "Children's Activities", "Toys"],
    "Fitness": ["Gym Membership", "Fitness Equipment", "Workout Clothes", "Personal Trainer", "Fitness App"],
    "Electronics": ["Apple Store", "Best Buy", "Microsoft Store", "Samsung Store", "Electronic Parts"],
    "Clothing": ["Nike", "Adidas", "Gap", "Old Navy", "Macy's", "Nordstrom", "H&M", "Zara"],
    "Beauty": ["Sephora", "Ulta", "Salon", "Spa", "Cosmetics Store"],
    "Hobbies": ["Hobby Store", "Craft Supplies", "Musical Instruments", "Sports Equipment", "Books"],
    "Gifts": ["Gift Shop", "Online Gift Store", "Flower Shop", "Jewelry Store", "Department Store"]
}

# Description templates for transaction types
TRANSACTION_DESCRIPTIONS = {
    "Purchase": [
        "Purchase at {merchant}",
        "{merchant} purchase",
        "Retail purchase - {merchant}",
        "Purchase - {merchant}",
        "Shopping at {merchant}"
    ],
    "Transfer": [
        "Transfer to account",
        "Money transfer",
        "Account transfer",
        "Transfer - {merchant}",
        "Electronic transfer"
    ],
    "Withdrawal": [
        "ATM withdrawal",
        "Cash withdrawal",
        "Withdrawal at {merchant}",
        "Bank withdrawal",
        "Cash back"
    ],
    "Deposit": [
        "Direct deposit",
        "Check deposit",
        "Mobile deposit",
        "Deposit at ATM",
        "Electronic deposit",
        "Salary deposit",
        "Paycheck deposit"
    ],
    "Payment": [
        "Bill payment - {merchant}",
        "Monthly payment to {merchant}",
        "Automatic payment - {merchant}",
        "Payment for services",
        "Utility payment - {merchant}",
        "Subscription payment - {merchant}",
        "Loan payment"
    ],
    "Refund": [
        "Refund from {merchant}",
        "Purchase refund",
        "Credit - {merchant}",
        "Return refund",
        "Service refund - {merchant}"
    ]
}

# Add specific keyword-containing descriptions for overdraft detection
OVERDRAFT_DESCRIPTIONS = [
    "Overdraft fee",
    "Overdraft protection fee",
    "Overdraft transfer fee",
    "Overdraft coverage",
    "NSF fee",
    "Insufficient funds fee"
]

# Helper functions
def generate_customer_id(index: int) -> str:
    """Generate a unique customer ID."""
    # Use the exact same format as in the original sample data: CUSTOMER1, CUSTOMER2, etc.
    return f"CUSTOMER{index + 1}"

def generate_goal_id(customer_id: str, index: int) -> str:
    """Generate a unique goal ID."""
    # Follow original format: GOAL1, GOAL2, etc.
    global global_goal_counter
    global_goal_counter += 1
    return f"GOAL{global_goal_counter}"

def generate_budget_id(customer_id: str, index: int) -> str:
    """Generate a unique budget ID."""
    # Follow original format: BUDGET1, BUDGET2, etc.
    global global_budget_counter
    global_budget_counter += 1
    return f"BUDGET{global_budget_counter}"

def generate_subscription_id(customer_id: str, index: int) -> str:
    """Generate a unique subscription ID."""
    # Follow original format: SUB1, SUB2, etc.
    global global_subscription_counter
    global_subscription_counter += 1
    return f"SUB{global_subscription_counter}"

def generate_transaction_id(customer_id: str, index: int) -> str:
    """Generate a unique transaction ID."""
    # Follow original format: TX12345, etc.
    return f"TX{random.randint(10000, 99999)}"

def generate_account_id(customer_id: str) -> str:
    """Generate a unique account ID."""
    # Follow original format: ACC1, etc.
    customer_number = customer_id.replace("CUSTOMER", "")
    return f"ACC{customer_number}"

def random_date(start_date: datetime.datetime, end_date: datetime.datetime) -> datetime.datetime:
    """Generate a random date between start_date and end_date."""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + datetime.timedelta(days=random_number_of_days)

def random_date_time(start_date: datetime.datetime, end_date: datetime.datetime) -> str:
    """Generate a random date and time between start_date and end_date."""
    random_date = start_date + datetime.timedelta(
        days=random.randint(0, (end_date - start_date).days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    return random_date.strftime("%m/%d/%Y %H:%M")

def generate_random_name(gender: str = None) -> str:
    """Generate a random full name."""
    first_names_male = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles", 
                         "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Andrew", "Paul", "Joshua"]
    first_names_female = ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen", 
                           "Lisa", "Nancy", "Betty", "Margaret", "Sandra", "Ashley", "Kimberly", "Emily", "Donna", "Michelle"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor", 
                   "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson",
                   "Clark", "Rodriguez", "Lewis", "Lee", "Walker", "Hall", "Allen", "Young", "Hernandez", "King"]
    
    if gender is None:
        gender = random.choice(["male", "female"])
    
    if gender == "male":
        first_name = random.choice(first_names_male)
    else:
        first_name = random.choice(first_names_female)
    
    last_name = random.choice(last_names)
    
    return f"{first_name} {last_name}"

def ensure_directory(path: str):
    """Ensure that a directory exists, creating it if necessary."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def format_date(date_obj: datetime.datetime) -> str:
    """Format a date as MM/DD/YYYY."""
    return date_obj.strftime("%m/%d/%Y")

def generate_asset_allocation(risk_category: str) -> Dict[str, float]:
    """Generate asset allocation percentages based on risk category."""
    profile = INVESTMENT_PROFILES[risk_category]
    allocation = {}
    
    # First generate the raw random values within their ranges
    for asset, range_tuple in profile.items():
        min_val, max_val = range_tuple
        if min_val == max_val:
            allocation[asset] = min_val
        else:
            allocation[asset] = round(random.uniform(min_val, max_val), 1)
    
    # Normalize to ensure it adds up to 100%
    total = sum(allocation.values())
    if total != 100:
        scale_factor = 100 / total
        allocation = {asset: round(pct * scale_factor, 1) for asset, pct in allocation.items()}
        
        # Handle any rounding errors by adjusting the largest allocation
        total = sum(allocation.values())
        if total != 100:
            diff = 100 - total
            largest_asset = max(allocation.items(), key=lambda x: x[1])[0]
            allocation[largest_asset] = round(allocation[largest_asset] + diff, 1)
    
    return allocation

def generate_random_allocation() -> Dict[str, float]:
    """Generate a random asset allocation (possibly not optimal)."""
    allocation = {
        "Cash": round(random.uniform(0, 100), 1),
        "Bonds": round(random.uniform(0, 100), 1),
        "Large Cap": round(random.uniform(0, 100), 1),
        "Mid Cap": round(random.uniform(0, 100), 1),
        "Small Cap": round(random.uniform(0, 100), 1),
        "International": round(random.uniform(0, 100), 1),
        "Real Estate": round(random.uniform(0, 100), 1),
        "Commodities": round(random.uniform(0, 100), 1)
    }
    
    # Normalize to 100%
    total = sum(allocation.values())
    if total > 0:  # Avoid division by zero
        scale_factor = 100 / total
        allocation = {asset: round(pct * scale_factor, 1) for asset, pct in allocation.items()}
        
        # Handle any rounding errors
        total = sum(allocation.values())
        if total != 100:
            diff = 100 - total
            largest_asset = max(allocation.items(), key=lambda x: x[1])[0]
            allocation[largest_asset] = round(allocation[largest_asset] + diff, 1)
    
    return allocation

def generate_risk_score(risk_profile: str) -> int:
    """Generate a risk score (1-100) based on the risk profile."""
    if risk_profile == "Very Low":
        return random.randint(1, 20)
    elif risk_profile == "Low":
        return random.randint(21, 40)
    elif risk_profile == "Medium":
        return random.randint(41, 60)
    elif risk_profile == "High":
        return random.randint(61, 80)
    else:  # Very High
        return random.randint(81, 100)

def map_risk_profile_to_category(risk_profile: str) -> str:
    """Map risk profile to a risk category."""
    if risk_profile == "Very Low":
        return "Risk Averse"
    elif risk_profile == "Low":
        return "Conservative"
    elif risk_profile == "Medium":
        return "Balanced"
    elif risk_profile == "High":
        return "Growth"
    else:  # Very High
        return "Aggressive"

def generate_investment_experience(risk_category: str) -> str:
    """Generate investment experience level based on risk category."""
    experience_mapping = {
        "Risk Averse": ["None", "Beginner"],
        "Conservative": ["Beginner", "Limited"],
        "Balanced": ["Limited", "Moderate"],
        "Growth": ["Moderate", "Experienced"],
        "Aggressive": ["Experienced", "Advanced"]
    }
    return random.choice(experience_mapping[risk_category])

def generate_time_horizon(age: int, risk_category: str) -> str:
    """Generate investment time horizon based on age and risk category."""
    if age < 30:
        return "Long-term"
    elif age < 45:
        if risk_category in ["Growth", "Aggressive"]:
            return "Long-term"
        else:
            return "Mid-term"
    elif age < 60:
        if risk_category == "Aggressive":
            return "Mid-term"
        else:
            return "Short-term"
    else:
        return "Short-term"

def calculate_progress_percentage(current: float, target: float) -> float:
    """Calculate progress percentage towards a goal."""
    if target == 0:
        return 0  # Avoid division by zero
    progress = (current / target) * 100
    return round(progress, 1)

def generate_timeline_type(months: int) -> str:
    """Determine timeline type based on number of months."""
    if months <= 12:
        return "Short-term"
    elif months <= 36:
        return "Medium-term"
    else:
        return "Long-term"

def generate_merchant_for_category(category: str) -> str:
    """Generate a merchant name appropriate for the given category."""
    if category in MERCHANT_CATEGORIES:
        return random.choice(MERCHANT_CATEGORIES[category])
    else:
        # Default merchants if category not found
        return random.choice(["Amazon", "Walmart", "Target", "Local Store", "Online Retailer"])

def generate_priority_for_goal(goal_type: str) -> str:
    """Generate priority level for a goal type."""
    priority_mapping = {
        "Emergency Fund": "Very High",
        "Debt Repayment": "Very High",
        "Retirement": "High",
        "Home Purchase": "High",
        "Education": "High",
        "Medical Expenses": "High",
        "Car Purchase": "Medium",
        "Wedding": "Medium",
        "Starting Business": "High",
        "Travel": "Low",
        "Real Estate Investment": "Medium"
    }
    
    return priority_mapping.get(goal_type, "Medium")

def generate_goal_amount(goal_type: str, income: float, monthly_expenses: float) -> float:
    """Generate an appropriate goal amount based on the goal type and user's financial situation."""
    template = GOAL_TEMPLATES.get(goal_type, {})
    
    if goal_type == "Emergency Fund":
        # Emergency fund is typically 3-6 months of expenses
        months = random.uniform(template.get("amount_factor", (3, 6))[0], template.get("amount_factor", (3, 6))[1])
        return round(monthly_expenses * months, 2)
    
    elif goal_type == "Home Purchase":
        # Home purchase down payment is typically 10-20% of home value
        home_value = income * random.uniform(template.get("home_value_factor", (3, 5))[0], template.get("home_value_factor", (3, 5))[1])
        down_payment_pct = random.uniform(template.get("amount_factor", (0.1, 0.2))[0], template.get("amount_factor", (0.1, 0.2))[1])
        return round(home_value * down_payment_pct, 2)
    
    elif goal_type == "Retirement":
        # Retirement is typically 10-20x annual income
        factor = random.uniform(template.get("amount_factor", (10, 20))[0], template.get("amount_factor", (10, 20))[1])
        return round(income * factor, 2)
    
    else:
        # Other goals have fixed amount ranges
        min_amount, max_amount = template.get("amount_fixed_range", (5000, 50000))
        return round(random.uniform(min_amount, max_amount), 2)

def generate_description(transaction_type: str, merchant_name: str) -> str:
    """Generate a description for a transaction based on its type and merchant."""
    # Sometimes generate an overdraft fee description
    if random.random() < 0.02:  # 2% chance of being an overdraft
        return random.choice(OVERDRAFT_DESCRIPTIONS)

    description_templates = TRANSACTION_DESCRIPTIONS.get(transaction_type, ["{merchant} transaction"])
    description = random.choice(description_templates)
    return description.format(merchant=merchant_name)

def generate_user_data() -> List[Dict[str, Any]]:
    """Generate data for users based on defined archetypes."""
    users = []
    
    for i in range(NUM_USERS):
        # Select a random archetype
        archetype = random.choice(USER_ARCHETYPES)
        
        # Generate basic user info
        customer_id = generate_customer_id(i)
        name = generate_random_name()
        age = random.randint(archetype["age_range"][0], archetype["age_range"][1])
        income = round(random.uniform(archetype["income_range"][0], archetype["income_range"][1]), 2)
        risk_profile = archetype["risk_profile"]
        risk_category = archetype["risk_category"]
        risk_score = generate_risk_score(risk_profile)
        marital_status = archetype["marital_status"]
        employment_type = archetype["employment"]
        language = archetype["language"]
        
        # Generate financial metrics
        savings_balance = round(income * random.uniform(archetype["savings_ratio"][0], archetype["savings_ratio"][1]), 2)
        checking_balance = round(income * random.uniform(archetype["checking_ratio"][0], archetype["checking_ratio"][1]), 2)
        
        # Generate investment details
        investment_experience = generate_investment_experience(risk_category)
        time_horizon = generate_time_horizon(age, risk_category)
        portfolio_value = round(savings_balance * random.uniform(0.5, 2.0), 2)
        
        # Store user data
        user = {
            "customer_id": customer_id,
            "name": name,
            "age": age,
            "income": income,
            "risk_profile": risk_profile,
            "risk_category": risk_category,
            "risk_score": risk_score,
            "marital_status": marital_status,
            "employment_type": employment_type,
            "language": language,
            "savings_balance": savings_balance,
            "checking_balance": checking_balance,
            "investment_experience": investment_experience,
            "time_horizon": time_horizon,
            "portfolio_value": portfolio_value,
            "archetype_name": archetype["name"],
            "goals": archetype["goals"],
            "main_goal": archetype["main_goal"],
            "budget_categories": archetype["budget_categories"],
            # Will be populated later
            "financial_goals": [],
            "budget_data": [],
            "subscriptions": [],
            "transactions": [],
            "asset_allocation": generate_asset_allocation(risk_category)
        }
        
        users.append(user)
    
    return users

def generate_goals_data(users: List[Dict[str, Any]]) -> None:
    """Generate financial goals for each user and add to their user dictionary."""
    global global_goal_counter
    
    for user in users:
        # Determine how many goals to create (1-4)
        num_goals = min(len(user["goals"]), random.randint(1, 4))
        
        # Ensure the main goal is included
        selected_goals = [user["main_goal"]]
        
        # Select additional random goals
        other_goals = [g for g in user["goals"] if g != user["main_goal"]]
        if other_goals and num_goals > 1:
            additional_goals = random.sample(other_goals, min(len(other_goals), num_goals - 1))
            selected_goals.extend(additional_goals)
        
        # Calculate monthly expenses (rough estimate for goal amount calculations)
        monthly_expenses = user["income"] / 12 * 0.7  # Assuming 70% of income goes to expenses
        
        # Generate each goal
        for i, goal_type in enumerate(selected_goals):
            goal_id = generate_goal_id("", i)  # We don't need customer_id in goal_id
            
            # Generate goal amount
            target_amount = generate_goal_amount(goal_type, user["income"], monthly_expenses)
            
            # Generate timeline
            template = GOAL_TEMPLATES.get(goal_type, {})
            timeline_months = random.randint(template.get("timeline_range", (6, 36))[0], 
                                            template.get("timeline_range", (6, 36))[1])
            
            # Generate dates
            start_date = random_date(CURRENT_DATE - relativedelta(months=6), CURRENT_DATE)
            target_date = start_date + relativedelta(months=timeline_months)
            last_updated = random_date(start_date, CURRENT_DATE)
            
            # Generate progress
            progress_percentage = random.uniform(0, min(90, (CURRENT_DATE - start_date).days / (target_date - start_date).days * 100))
            current_savings = round(target_amount * progress_percentage / 100, 2)
            
            # Calculate monthly contribution
            remaining_months = max(1, (target_date - CURRENT_DATE).days / 30)
            remaining_amount = target_amount - current_savings
            monthly_contribution = round(remaining_amount / remaining_months, 2)
            
            # Priority
            priority = generate_priority_for_goal(goal_type)
            if goal_type == user["main_goal"]:
                priority = max(priority, "High")  # Main goal is at least High priority
            
            timeline_type = template.get("timeline_type", generate_timeline_type(timeline_months))
            
            # Create goal dictionary
            goal = {
                "goal_id": goal_id,
                "customer_id": user["customer_id"].lower(),  # Changed to lowercase to match original format
                "goal_name": goal_type,
                "target_amount": target_amount,
                "current_savings": current_savings,
                "target_date": format_date(target_date),
                "goal_type": goal_type,
                "goal_timeline": timeline_type,
                "monthly_contribution": monthly_contribution,
                "priority": priority,
                "start_date": format_date(start_date),
                "last_updated": format_date(last_updated),
                "automatic_contribution": random.choice([True, False]),
                "progress_percentage": round(progress_percentage, 1),
                "months_remaining": round(remaining_months)
            }
            
            # Add goal to user's goals list
            user["financial_goals"].append(goal)

def generate_budget_data(users: List[Dict[str, Any]]) -> None:
    """Generate budget data for each user and add to their user dictionary."""
    for user in users:
        global global_budget_counter
        
        # Select categories from user's archetype
        num_categories = min(len(user["budget_categories"]), random.randint(3, 6))
        selected_categories = random.sample(user["budget_categories"], num_categories)
        
        for i, category in enumerate(selected_categories):
            global_budget_counter += 1
            budget_id = f"BUDGET{global_budget_counter}"
            
            # Calculate budget limit based on category and income
            category_pct_range = BUDGET_CATEGORIES.get(category, (0.05, 0.1))
            budget_pct = random.uniform(category_pct_range[0], category_pct_range[1])
            monthly_limit = round(user["income"] / 12 * budget_pct, 2)
            
            # Calculate how much is spent so far
            utilization_pct = random.uniform(30, 95)  # 30-95% utilized
            spent_so_far = round(monthly_limit * utilization_pct / 100, 2)
            
            # Create budget entry
            budget_entry = {
                "budget_id": budget_id,
                "customer_id": user["customer_id"],
                "category": category,
                "monthly_limit": monthly_limit,
                "spent_so_far": spent_so_far,
                "% Utilized": round(utilization_pct, 2)  # Keep the original column name
            }
            
            # Add to user's budget data
            user["budget_data"].append(budget_entry)

def generate_subscription_data(users: List[Dict[str, Any]]) -> None:
    """Generate subscription data for each user and add to their user dictionary."""
    for user in users:
        global global_subscription_counter
        
        # Determine number of subscriptions (1-6)
        num_subscriptions = random.randint(1, 6)
        
        # Select random subscription services
        selected_services = random.sample(SUBSCRIPTION_SERVICES, num_subscriptions)
        
        for i, service in enumerate(selected_services):
            global_subscription_counter += 1
            subscription_id = f"SUB{global_subscription_counter}"
            
            # Calculate amount within the service's range
            amount = round(random.uniform(service["amount_range"][0], service["amount_range"][1]), 2)
            
            # Generate last billed date (within the last 30 days)
            last_billed_date = random_date(CURRENT_DATE - datetime.timedelta(days=30), CURRENT_DATE)
            
            # Create subscription entry
            subscription = {
                "subscription_id": subscription_id,
                "customer_id": user["customer_id"],
                "merchant_name": service["name"],
                "amount": amount,
                "frequency": service["frequency"],
                "last_billed_date": format_date(last_billed_date)
            }
            
            # Add to user's subscriptions
            user["subscriptions"].append(subscription)

def generate_transaction_data(users: List[Dict[str, Any]]) -> None:
    """Generate transaction data for each user and add to their user dictionary."""
    global global_transaction_counter
    
    for user in users:
        # Create a checking account ID
        account_id = generate_account_id(user["customer_id"])
        
        # Determine number of transactions (10-30)
        num_transactions = random.randint(10, 30)
        
        # Start with the current checking balance
        current_balance = user["checking_balance"]
        
        # Set date range for transactions (last 90 days)
        end_date = CURRENT_DATE
        start_date = end_date - datetime.timedelta(days=90)
        
        # Generate transactions
        transactions = []
        for i in range(num_transactions):
            global_transaction_counter += 1
            transaction_id = f"TX{random.randint(10000, 99999)}"
            
            # Randomly select a transaction type
            transaction_type = random.choice(TRANSACTION_TYPES)
            
            # Determine if this is an inflow or outflow
            is_outflow = transaction_type in ["Purchase", "Withdrawal", "Payment"]
            
            # Generate transaction amount
            if is_outflow:
                if transaction_type == "Purchase":
                    # Purchases are typically smaller
                    amount = round(random.uniform(10, 200), 2)
                else:
                    # Withdrawals and payments can be larger
                    amount = round(random.uniform(50, 500), 2)
            else:
                # Inflows (deposits, transfers in, refunds)
                amount = round(random.uniform(100, 1000), 2)
            
            # Select a merchant category
            if transaction_type == "Purchase":
                merchant_category = random.choice(list(MERCHANT_CATEGORIES.keys()))
            else:
                merchant_category = "Transfer" if transaction_type == "Transfer" else random.choice(list(MERCHANT_CATEGORIES.keys()))
            
            # Generate merchant
            merchant_id = f"MER{random.randint(100, 999)}"
            merchant_name = generate_merchant_for_category(merchant_category)
            
            # Generate transaction date and time
            transaction_date_time = random_date_time(start_date, end_date)
            
            # Calculate closing balance
            if is_outflow:
                closing_balance = round(current_balance - amount, 2)
            else:
                closing_balance = round(current_balance + amount, 2)
            
            # Update current balance for next transaction
            current_balance = closing_balance
            
            # Additional fields
            transaction_mode = random.choice(["Online", "Mobile", "Offline"])
            transaction_status = random.choice(["Completed", "Pending", "Failed"])
            transaction_location = f"Location {random.randint(1, 50)}"
            payment_mode = random.choice(["Debit Card", "Credit Card", "Wallet", "Net Banking"])
            
            # Generate a description for the transaction
            description = generate_description(transaction_type, merchant_name)
            
            # Create transaction entry
            transaction = {
                "transaction_id": transaction_id,
                "account_number": account_id,
                "customer_id": user["customer_id"],
                "transaction_type": transaction_type,
                "transaction_date_time": transaction_date_time,
                "transaction_amount": amount,
                "closing_balance": closing_balance,
                "transaction_mode": transaction_mode,
                "transaction_status": transaction_status,
                "merchant_category_code": merchant_category,
                "merchant_id": merchant_id,
                "merchant_name": merchant_name,
                "transaction_location": transaction_location,
                "payment_mode": payment_mode,
                "description": description  # Add description for the transaction analysis agent
            }
            
            transactions.append(transaction)
        
        # Sort transactions by date (newest first)
        transactions.sort(key=lambda x: datetime.datetime.strptime(x["transaction_date_time"], "%m/%d/%Y %H:%M"), reverse=True)
        
        # Add to user's transactions
        user["transactions"] = transactions

def generate_asset_allocation_data(users: List[Dict[str, Any]]) -> None:
    """Generate asset allocation data for each user."""
    for user in users:
        # User's overall portfolio allocation already generated
        
        # Generate goal-specific allocations
        for goal in user["financial_goals"]:
            # Determine if this goal should have a different allocation
            if goal["goal_name"] in ["Emergency Fund", "Car Purchase", "Travel", "Wedding"]:
                # Short-term goals should be more conservative
                if random.random() < 0.7:  # 70% chance of being more conservative
                    goal_allocation = {
                        "Cash": round(random.uniform(60, 100), 1),
                        "Bonds": round(random.uniform(0, 40), 1),
                        "Large Cap": round(random.uniform(0, 10), 1),
                        "Mid Cap": 0,
                        "Small Cap": 0,
                        "International": 0,
                        "Real Estate": 0,
                        "Commodities": 0
                    }
                else:
                    # Generate random allocation (possibly not aligned with recommendations)
                    goal_allocation = generate_random_allocation()
            else:
                if random.random() < 0.6:  # 60% chance of being aligned with overall allocation
                    goal_allocation = user["asset_allocation"]
                else:
                    # Generate random allocation
                    goal_allocation = generate_random_allocation()
            
            # Normalize to 100%
            total = sum(goal_allocation.values())
            if total > 0:
                scale_factor = 100 / total
                goal_allocation = {asset: round(pct * scale_factor, 1) for asset, pct in goal_allocation.items()}
                
                # Handle any rounding errors
                total = sum(goal_allocation.values())
                if total != 100:
                    diff = 100 - total
                    largest_asset = max(goal_allocation.items(), key=lambda x: x[1])[0]
                    goal_allocation[largest_asset] = round(goal_allocation[largest_asset] + diff, 1)
            
            # Add allocation to goal
            goal["allocation"] = goal_allocation

def write_csv_files(users: List[Dict[str, Any]], output_path: str) -> None:
    """Write all data to CSV files in the specified output directory."""
    ensure_directory(output_path)
    
    # Write user profile data
    user_profile_data = []
    for user in users:
        user_profile_data.append({
            "Customer ID": user["customer_id"],
            "Name": user["name"],
            "Age": user["age"],
            "Income": user["income"],
            "Risk Profile": user["risk_profile"],
            "Preferred Language": user["language"],
            "Savings Balance": user["savings_balance"],
            "Checking Balance": user["checking_balance"],
            "Marital Status": user["marital_status"],
            "Employment Type": user["employment_type"]
        })
    
    with open(os.path.join(output_path, "user_profile_data.csv"), "w", newline="") as f:
        if user_profile_data:
            writer = csv.DictWriter(f, fieldnames=user_profile_data[0].keys())
            writer.writeheader()
            writer.writerows(user_profile_data)
    
    # Write financial goals data
    financial_goals_data = []
    for user in users:
        for goal in user["financial_goals"]:
            # Convert customer_id to lowercase to match original format in goals table
            financial_goals_data.append({
                "Goal ID": goal["goal_id"],
                "Customer ID": user["customer_id"].lower(),
                "Goal Name": goal["goal_name"],
                "Target Amount": goal["target_amount"],
                "Current Savings": goal["current_savings"],
                "Target Date": goal["target_date"],
                "Goal Type": goal["goal_type"],
                "Goal Timeline": goal["goal_timeline"],
                "Progress (%)": goal["progress_percentage"]  # Add progress percentage
            })
    
    with open(os.path.join(output_path, "financial_goals_data.csv"), "w", newline="") as f:
        if financial_goals_data:
            writer = csv.DictWriter(f, fieldnames=financial_goals_data[0].keys())
            writer.writeheader()
            writer.writerows(financial_goals_data)
    
    # Write budget data
    budget_data = []
    for user in users:
        for budget in user["budget_data"]:
            budget_data.append({
                "Budget ID": budget["budget_id"],
                "Customer ID": budget["customer_id"],
                "Category": budget["category"],
                "Monthly Limit": budget["monthly_limit"],
                "Spent So Far": budget["spent_so_far"],
                "% Utilized": budget["% Utilized"]  # Use the original column name
            })
    
    with open(os.path.join(output_path, "budget_data.csv"), "w", newline="") as f:
        if budget_data:
            writer = csv.DictWriter(f, fieldnames=budget_data[0].keys())
            writer.writeheader()
            writer.writerows(budget_data)
    
    # Write subscription data
    subscription_data = []
    for user in users:
        for subscription in user["subscriptions"]:
            subscription_data.append({
                "Subscription ID": subscription["subscription_id"],
                "Customer ID": subscription["customer_id"],
                "Merchant Name": subscription["merchant_name"],
                "Amount": subscription["amount"],
                "Frequency": subscription["frequency"],
                "Last Billed Date": subscription["last_billed_date"]
            })
    
    with open(os.path.join(output_path, "subscription_data.csv"), "w", newline="") as f:
        if subscription_data:
            writer = csv.DictWriter(f, fieldnames=subscription_data[0].keys())
            writer.writeheader()
            writer.writerows(subscription_data)
    
    # Write transaction data - Using exact column names expected by the agent
    transaction_data = []
    for user in users:
        for txn in user["transactions"]:
            # Create a new transaction entry with the exact column names the agent expects
            transaction_entry = {
                "Transaction ID": txn["transaction_id"],
                "Account Number": txn["account_number"],
                "Customer ID": txn["customer_id"],  # Exactly as the agent expects it
                "Transaction Type": txn["transaction_type"],
                "Transaction Date and Time": txn["transaction_date_time"],
                "Transaction Amount": txn["transaction_amount"],
                "Closing Balance": txn["closing_balance"],
                "Transaction Mode": txn["transaction_mode"],
                "Transaction Status": txn["transaction_status"],
                "Merchant Category Code": txn["merchant_category_code"],
                "Merchant ID": txn["merchant_id"],
                "Merchant Name": txn["merchant_name"],
                "Transaction Location": txn["transaction_location"],
                "Payment Mode": txn["payment_mode"],
                "Description": txn["description"]  # From our earlier addition
            }
            
            # Add merchant category based on merchant category code (keep original data intact)
            transaction_entry["Merchant Category"] = txn["merchant_category_code"]
            
            transaction_data.append(transaction_entry)
    
    with open(os.path.join(output_path, "transactions_data.csv"), "w", newline="") as f:
        if transaction_data:
            writer = csv.DictWriter(f, fieldnames=transaction_data[0].keys())
            writer.writeheader()
            writer.writerows(transaction_data)
    
    # Write asset allocation data
    asset_allocation_data = []
    for user in users:
        asset_allocation_data.append({
            "Customer ID": user["customer_id"],
            "Total Portfolio Value": user["portfolio_value"],
            "Cash %": user["asset_allocation"]["Cash"],
            "Bonds %": user["asset_allocation"]["Bonds"],
            "Large Cap %": user["asset_allocation"]["Large Cap"],
            "Mid Cap %": user["asset_allocation"]["Mid Cap"],
            "Small Cap %": user["asset_allocation"]["Small Cap"],
            "International %": user["asset_allocation"]["International"],
            "Real Estate %": user["asset_allocation"]["Real Estate"],
            "Commodities %": user["asset_allocation"]["Commodities"],
            "Last Rebalanced": format_date(random_date(CURRENT_DATE - datetime.timedelta(days=90), CURRENT_DATE))
        })
    
    with open(os.path.join(output_path, "current_asset_allocation.csv"), "w", newline="") as f:
        if asset_allocation_data:
            writer = csv.DictWriter(f, fieldnames=asset_allocation_data[0].keys())
            writer.writeheader()
            writer.writerows(asset_allocation_data)
    
    # Write goal-specific asset allocation data
    goal_allocation_data = []
    for user in users:
        for goal in user["financial_goals"]:
            if "allocation" in goal:
                goal_allocation_data.append({
                    "Goal ID": goal["goal_id"],
                    "Customer ID": user["customer_id"].lower(),
                    "Total Goal Portfolio": goal["current_savings"],
                    "Cash %": goal["allocation"]["Cash"],
                    "Bonds %": goal["allocation"]["Bonds"],
                    "Large Cap %": goal["allocation"]["Large Cap"],
                    "Mid Cap %": goal["allocation"]["Mid Cap"],
                    "Small Cap %": goal["allocation"]["Small Cap"],
                    "International %": goal["allocation"]["International"],
                    "Real Estate %": goal["allocation"]["Real Estate"],
                    "Commodities %": goal["allocation"]["Commodities"]
                })
    
    with open(os.path.join(output_path, "goal_specific_allocations.csv"), "w", newline="") as f:
        if goal_allocation_data:
            writer = csv.DictWriter(f, fieldnames=goal_allocation_data[0].keys())
            writer.writeheader()
            writer.writerows(goal_allocation_data)
    
    # Write expanded risk profile data
    risk_profile_data = []
    for user in users:
        risk_profile_data.append({
            "Customer ID": user["customer_id"],
            "Name": user["name"],
            "Age": user["age"],
            "Income": user["income"],
            "Risk Profile": user["risk_profile"],
            "Risk Score": user["risk_score"],
            "Risk Category": user["risk_category"],
            "Investment Experience": user["investment_experience"],
            "Time Horizon": user["time_horizon"]
        })
    
    with open(os.path.join(output_path, "expanded_risk_profiles.csv"), "w", newline="") as f:
        if risk_profile_data:
            writer = csv.DictWriter(f, fieldnames=risk_profile_data[0].keys())
            writer.writeheader()
            writer.writerows(risk_profile_data)
    
    # Write asset allocation matrix
    asset_allocation_matrix = []
    for risk_category in ["Risk Averse", "Conservative", "Balanced", "Growth", "Aggressive"]:
        for timeline in ["Short-term", "Medium-term", "Long-term"]:
            allocation = generate_asset_allocation(risk_category)
            asset_allocation_matrix.append({
                "Risk Category": risk_category,
                "Goal Timeline": timeline,
                "Cash %": allocation["Cash"],
                "Bonds %": allocation["Bonds"],
                "Large Cap %": allocation["Large Cap"],
                "Mid Cap %": allocation["Mid Cap"],
                "Small Cap %": allocation["Small Cap"],
                "International %": allocation["International"],
                "Real Estate %": allocation["Real Estate"],
                "Commodities %": allocation["Commodities"]
            })
    
    with open(os.path.join(output_path, "asset_allocation_matrix.csv"), "w", newline="") as f:
        if asset_allocation_matrix:
            writer = csv.DictWriter(f, fieldnames=asset_allocation_matrix[0].keys())
            writer.writeheader()
            writer.writerows(asset_allocation_matrix)
    
    # Write enhanced goal data
    enhanced_goal_data = []
    for user in users:
        for goal in user["financial_goals"]:
            enhanced_goal_data.append({
                "Goal ID": goal["goal_id"],
                "Customer ID": user["customer_id"].lower(),
                "Goal Name": goal["goal_name"],
                "Target Amount": goal["target_amount"],
                "Current Savings": goal["current_savings"],
                "Target Date": goal["target_date"],
                "Goal Type": goal["goal_type"],
                "Goal Timeline": goal["goal_timeline"],
                "Monthly Contribution": goal["monthly_contribution"],
                "Priority": goal["priority"],
                "Start Date": goal["start_date"],
                "Last Updated": goal["last_updated"],
                "Automatic Contribution": "Yes" if goal["automatic_contribution"] else "No",
                "Progress (%)": goal["progress_percentage"]
            })
    
    with open(os.path.join(output_path, "enhanced_goal_data.csv"), "w", newline="") as f:
        if enhanced_goal_data:
            writer = csv.DictWriter(f, fieldnames=enhanced_goal_data[0].keys())
            writer.writeheader()
            writer.writerows(enhanced_goal_data)

def main():
    """Main function to generate and save all synthetic data."""
    print("Starting financial data generation...")
    
    # Reset global counters
    global global_goal_counter, global_budget_counter, global_subscription_counter, global_transaction_counter
    global_goal_counter = 0
    global_budget_counter = 0
    global_subscription_counter = 0
    global_transaction_counter = 0
    
    # Generate user data
    users = generate_user_data()
    print(f"Generated data for {len(users)} users")
    
    # Generate additional data types
    generate_goals_data(users)
    print("Generated financial goals")
    
    generate_budget_data(users)
    print("Generated budget data")
    
    generate_subscription_data(users)
    print("Generated subscription data")
    
    generate_transaction_data(users)
    print("Generated transaction data")
    
    generate_asset_allocation_data(users)
    print("Generated asset allocation data")
    
    # Write data to CSV files
    write_csv_files(users, BASE_DATA_PATH)
    print(f"All data written to {BASE_DATA_PATH}")
    
    print("Data generation complete!")

if __name__ == "__main__":
    main()
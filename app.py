"""
Personal Finance Manager - Streamlit Application

This is the main application file for the Personal Finance Manager Streamlit frontend.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import sys

# Add parent directory to system path to import our agents
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import the Financial Advisor Agent
from agents.financial_advisor_agent import FinancialAdvisorAgent
from agents.transaction_analysis_agent import TransactionAnalysisAgent

# Path to data directory
DATA_PATH = "./synthetic_data"

# Initialize agents (only done once at startup)
@st.cache_resource
def get_financial_advisor():
    return FinancialAdvisorAgent(data_path=DATA_PATH)

@st.cache_resource
def get_transaction_agent():
    return TransactionAnalysisAgent(data_path=DATA_PATH)

# Load user data
@st.cache_data
def load_user_data():
    users_df = pd.read_csv(f"{DATA_PATH}/user_profile_data.csv")
    return users_df

@st.cache_data
def load_goals_data():
    goals_df = pd.read_csv(f"{DATA_PATH}/enhanced_goal_data.csv")
    return goals_df

@st.cache_data
def load_transactions_data():
    transactions_df = pd.read_csv(f"{DATA_PATH}/transactions_data.csv")
    return transactions_df

@st.cache_data
def load_budget_data():
    budget_df = pd.read_csv(f"{DATA_PATH}/budget_data.csv")
    return budget_df

@st.cache_data
def load_allocations_data():
    allocations_df = pd.read_csv(f"{DATA_PATH}/current_asset_allocation.csv")
    return allocations_df

def format_currency(value):
    """Format a numeric value as currency with commas and 2 decimal places."""
    try:
        return f"${value:,.2f}"
    except:
        return str(value)

def format_percentage(value):
    """Format a numeric value as a percentage with 1 decimal place."""
    try:
        return f"{value:.1f}%"
    except:
        return str(value)

def display_formatted_response(response):
    """Display a response with enhanced formatting."""
    # Split response by sections (if they exist)
    sections = response.split("\n\n")
    
    for section in sections:
        if ":" in section and len(section.split(":")[0]) < 50:
            # This might be a heading
            heading, content = section.split(":", 1)
            st.subheader(heading.strip())
            st.write(content.strip())
        else:
            # Regular paragraph or content
            st.write(section)

def display_goals_card(goal):
    """Display a goal in a well-formatted card."""
    with st.container():
        # Create a card-like container with border
        st.markdown(f"""
        <div style="border:1px solid #ddd; border-radius:5px; padding:10px; margin-bottom:10px;">
            <h3>{goal['Goal Name']}</h3>
            <p><strong>Target:</strong> ${goal['Target Amount']:,.2f} by {goal['Target Date']}</p>
            <p><strong>Current:</strong> ${goal['Current Savings']:,.2f} ({goal['Progress %']:.1f}% complete)</p>
            <p><strong>Monthly Contribution:</strong> ${goal['Monthly Contribution']:,.2f}</p>
            <div style="background-color:#f0f2f6; border-radius:3px; height:10px; width:100%;">
                <div style="background-color:#4e8df5; border-radius:3px; height:10px; width:{min(goal['Progress %'], 100)}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "selected_user" not in st.session_state:
        # Default to first user
        users_df = load_user_data()
        if not users_df.empty:
            st.session_state.selected_user = users_df['Customer ID'].iloc[0]
        else:
            st.session_state.selected_user = None
    
    if "nudges" not in st.session_state:
        st.session_state.nudges = None
    
    if "goals" not in st.session_state:
        st.session_state.goals = None

def user_selector():
    """Display user selection dropdown and return the selected user ID."""
    users_df = load_user_data()
    
    # Create a list of user options with name and ID
    user_options = [f"{row['Name']} ({row['Customer ID']})" for _, row in users_df.iterrows()]
    
    # Get the index of the currently selected user
    current_user_id = st.session_state.selected_user
    current_user_idx = 0
    for i, user_id in enumerate(users_df['Customer ID']):
        if user_id == current_user_id:
            current_user_idx = i
            break
    
    # Display the dropdown
    selected_option = st.sidebar.selectbox(
        "Select User",
        user_options,
        index=current_user_idx
    )
    
    # Extract the user ID from the selected option
    selected_user_id = selected_option.split("(")[1].split(")")[0]
    
    # Update session state if user changed
    if selected_user_id != st.session_state.selected_user:
        st.session_state.selected_user = selected_user_id
        st.session_state.chat_history = []  # Reset chat history for new user
        st.session_state.nudges = None  # Reset nudges for new user
    
    return selected_user_id

def display_user_info(user_id):
    """Display basic user information."""
    users_df = load_user_data()
    user_info = users_df[users_df['Customer ID'] == user_id].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Checking Balance", f"${user_info['Checking Balance']:,.2f}")
    with col2:
        st.metric("Savings Balance", f"${user_info['Savings Balance']:,.2f}")
    with col3:
        st.metric("Risk Profile", user_info['Risk Profile'])

def home_page():
    """Display the home page content."""
    st.title("Personal Finance Manager")
    
    st.markdown("""
    ## Welcome to Your Personal Finance Manager
    
    This tool helps you make smarter financial decisions through:
    
    - **Personalized Financial Advice**: Chat with our AI financial advisor for tailored guidance
    - **Spending Insights**: Receive nudges about your spending patterns and saving opportunities
    - **Goal Planning**: Set and track progress on your financial goals
    - **Data Visualization**: Visualize your financial data for better understanding
    
    ### Getting Started
    
    1. Select a user from the dropdown menu in the sidebar
    2. Navigate to different sections using the sidebar menu
    3. Explore your financial data and receive personalized recommendations
    
    ### Demo Features
    
    This demonstration showcases how AI can transform personal finance management through:
    
    - Natural language conversations with contextual awareness
    - Specialized financial agents working together to provide holistic advice
    - Data-driven insights that help optimize financial decision-making
    - Goal-based planning with actionable recommendations
    """)
    
    # Select a user
    selected_user = user_selector()
    
    # Display user info
    if selected_user:
        st.subheader(f"Current User: {selected_user}")
        display_user_info(selected_user)

def chatbot_page():
    """Display the chatbot interface with improved formatting."""
    st.title("Financial Advisor Chat")
    
    # Select a user
    selected_user = user_selector()
    if not selected_user:
        st.warning("Please select a user to continue.")
        return
    
    # Display user info
    display_user_info(selected_user)
    
    # Initialize or get the advisor agent
    advisor = get_financial_advisor()
    
    # Display chat history with improved formatting
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            # Use the improved formatter for assistant messages
            with st.chat_message("assistant"):
                display_formatted_response(message["content"])
    
    # Chat input
    if prompt := st.chat_input("How can I help with your finances today?"):
        # Display user message
        st.chat_message("user").write(prompt)
        
        # Add to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Get response from advisor
        with st.spinner("Thinking..."):
            response = advisor.process_query(prompt, selected_user)
        
        # Display assistant response with improved formatting
        with st.chat_message("assistant"):
            display_formatted_response(response)
        
        # Add to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})

def nudges_page():
    """Display financial nudges."""
    st.title("Financial Nudges")
    
    # Select a user
    selected_user = user_selector()
    if not selected_user:
        st.warning("Please select a user to continue.")
        return
    
    # Display user info
    display_user_info(selected_user)
    
    # Initialize transaction agent
    transaction_agent = get_transaction_agent()
    
    # Generate nudges button
    if st.button("Generate Nudges") or st.session_state.nudges:
        with st.spinner("Analyzing your transactions..."):
            if not st.session_state.nudges:
                # Only generate new nudges if we don't already have them
                nudges = transaction_agent.generate_nudges(selected_user)
                st.session_state.nudges = nudges
            else:
                nudges = st.session_state.nudges
        
        # Display nudges
        st.subheader("Here are your personalized financial nudges:")
        st.markdown(nudges)
    
    else:
        st.info("Click 'Generate Nudges' to receive personalized financial insights based on your transaction history.")
        
        # Example of what nudges look like
        st.subheader("Example Nudges:")
        st.markdown("""
        ### Subscription Management
        * **Observation**: You're currently spending $42.97 monthly on streaming services.
        * **Recommendation**: Consider consolidating to fewer services or using family plans.
        * **Potential Savings**: Up to $15/month or $180 annually.
        
        ### Dining Expense Pattern
        * **Observation**: Your dining expenses increased by 25% compared to last month.
        * **Recommendation**: Consider meal planning to reduce restaurant expenses.
        * **Potential Savings**: Reducing dining out by 2 meals/week could save approximately $80/month.
        """)

def goal_planning_page():
    """Display goal planning interface."""
    st.title("Goal Planning")
    
    # Select a user
    selected_user = user_selector()
    if not selected_user:
        st.warning("Please select a user to continue.")
        return
    
    # Display user info
    display_user_info(selected_user)
    
    # Initialize financial advisor
    advisor = get_financial_advisor()
    
    # Create tabs for different goal planning activities
    tab1, tab2, tab3 = st.tabs(["View Goals", "Create Goal", "Get Recommendations"])
    
    with tab1:
        st.subheader("Your Financial Goals")
        
        # Load goals data for the selected user
        goals_df = load_goals_data()
        user_goals = goals_df[goals_df['Customer ID'] == selected_user.lower()]
        
        if user_goals.empty:
            st.info("You don't have any financial goals yet. Create one in the 'Create Goal' tab.")
        else:
            # Display goals in cards
            for _, goal in user_goals.iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(f"{goal['Goal Name']}")
                        st.write(f"Target: ${goal['Target Amount']:,.2f} by {goal['Target Date']}")
                        st.write(f"Current Savings: ${goal['Current Savings']:,.2f}")
                        st.write(f"Monthly Contribution: ${goal['Monthly Contribution']:,.2f}")
                        st.write(f"Priority: {goal['Priority']}")
                    
                    with col2:
                        # Create a progress bar
                        progress = goal['Progress %'] / 100
                        st.metric("Progress", f"{goal['Progress %']}%")
                        st.progress(progress)
                    
                    st.divider()
    
    with tab2:
        st.subheader("Create New Financial Goal")
        
        # Goal creation form
        with st.form("goal_creation_form"):
            # Goal type selection
            goal_type = st.selectbox(
                "Goal Type",
                ["Retirement", "Home Purchase", "Education", "Emergency Fund", 
                 "Travel", "Car Purchase", "Wedding", "Medical Expenses"]
            )
            
            # Target amount
            target_amount = st.number_input("Target Amount ($)", min_value=100.0, value=10000.0, step=1000.0)
            
            # Current savings
            current_savings = st.number_input("Current Savings ($)", min_value=0.0, value=0.0, step=100.0)
            
            # Target date
            today = datetime.now()
            next_year = datetime(today.year + 1, today.month, today.day)
            target_date = st.date_input("Target Date", next_year)
            
            # Priority
            priority = st.selectbox(
                "Priority",
                ["Very High", "High", "Medium", "Low"]
            )
            
            # Submit button
            submitted = st.form_submit_button("Create Goal")
            
            if submitted:
                # Format the target date
                formatted_date = target_date.strftime("%m/%d/%Y")
                
                # Create a query for the advisor
                query = (
                    f"Create a new {goal_type} goal with a target amount of ${target_amount:,.2f}, "
                    f"current savings of ${current_savings:,.2f}, target date of {formatted_date}, "
                    f"and {priority} priority."
                )
                
                # Process the query
                with st.spinner("Creating goal..."):
                    response = advisor.process_query(query, selected_user)
                
                # Display the response
                st.success("Goal created successfully!")
                st.write(response)
    
    with tab3:
        st.subheader("Goal Recommendations")
        
        if st.button("Get Goal Recommendations"):
            # Create a query for the advisor
            query = "What recommendations do you have for my financial goals?"
            
            # Process the query
            with st.spinner("Analyzing your goals..."):
                response = advisor.process_query(query, selected_user)
            
            # Display the response
            st.write(response)
        else:
            st.info("Click 'Get Goal Recommendations' to receive personalized advice for optimizing your financial goals.")

def data_visualization_page():
    """Display data visualizations."""
    st.title("Financial Data Visualization")
    
    # Select a user
    selected_user = user_selector()
    if not selected_user:
        st.warning("Please select a user to continue.")
        return
    
    # Display user info
    display_user_info(selected_user)
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Spending Analysis", "Budget Status", "Asset Allocation", "Goal Progress"])
    
    # Load data
    transactions_df = load_transactions_data()
    user_transactions = transactions_df[transactions_df['Customer ID'] == selected_user]
    
    budget_df = load_budget_data()
    user_budget = budget_df[budget_df['Customer ID'] == selected_user]
    
    goals_df = load_goals_data()
    user_goals = goals_df[goals_df['Customer ID'] == selected_user.lower()]
    
    allocations_df = load_allocations_data()
    user_allocation = allocations_df[allocations_df['Customer ID'] == selected_user]
    
    with tab1:
        st.subheader("Spending Analysis")
        
        if user_transactions.empty:
            st.info("No transaction data available for visualization.")
        else:
            # Filter to only purchases and payments
            spending = user_transactions[user_transactions['Transaction Type'].isin(['Purchase', 'Payment'])]
            
            # Group by merchant category
            category_spending = spending.groupby('Merchant Category Code')['Transaction Amount'].sum().reset_index()
            category_spending = category_spending.sort_values('Transaction Amount', ascending=False)
            
            # Create bar chart
            fig = px.bar(
                category_spending,
                x='Merchant Category Code',
                y='Transaction Amount',
                title='Spending by Category',
                color='Merchant Category Code'
            )
            st.plotly_chart(fig)
            
            # Transaction history table
            st.subheader("Recent Transactions")
            # Sort by date (most recent first) and select recent transactions
            recent_transactions = user_transactions.sort_values('Transaction Date and Time', ascending=False).head(10)
            # Display only relevant columns
            display_cols = ['Transaction Date and Time', 'Merchant Name', 'Transaction Amount', 'Transaction Type']
            st.dataframe(recent_transactions[display_cols])
    
    with tab2:
        st.subheader("Budget Status")
        
        if user_budget.empty:
            st.info("No budget data available for visualization.")
        else:
            # Create budget utilization chart
            fig = go.Figure()
            
            for _, row in user_budget.iterrows():
                fig.add_trace(go.Bar(
                    x=[row['Category']],
                    y=[row['Monthly Limit']],
                    name='Monthly Limit',
                    marker_color='lightgrey'
                ))
                
                fig.add_trace(go.Bar(
                    x=[row['Category']],
                    y=[row['Spent So Far']],
                    name='Spent So Far',
                    marker_color='blue'
                ))
            
            fig.update_layout(
                title='Budget Utilization',
                barmode='overlay',
                yaxis_title='Amount ($)',
                legend_title='Budget vs. Actual'
            )
            
            st.plotly_chart(fig)
            
            # Budget table with utilization percentage
            st.subheader("Budget Details")
            st.dataframe(user_budget[['Category', 'Monthly Limit', 'Spent So Far', '% Utilized']])
    
    with tab3:
        st.subheader("Asset Allocation")
        
        if user_allocation.empty:
            st.info("No asset allocation data available for visualization.")
        else:
            # Extract allocation data
            allocation_row = user_allocation.iloc[0]
            
            # Create a dict of asset classes and percentages
            asset_classes = ['Cash %', 'Bonds %', 'Large Cap %', 'Mid Cap %', 
                             'Small Cap %', 'International %', 'Real Estate %', 'Commodities %']
            
            allocation_dict = {
                asset_class.replace(' %', ''): allocation_row[asset_class]
                for asset_class in asset_classes
            }
            
            # Create pie chart
            fig = px.pie(
                values=list(allocation_dict.values()),
                names=list(allocation_dict.keys()),
                title=f'Current Asset Allocation (Total: ${allocation_row["Total Portfolio Value"]:,.2f})'
            )
            st.plotly_chart(fig)
            
            # Display rebalance date
            st.info(f"Last rebalanced on: {allocation_row['Last Rebalanced']}")
    
    with tab4:
        st.subheader("Goal Progress")
        
        if user_goals.empty:
            st.info("No goals data available for visualization.")
        else:
            # Create progress chart
            fig = px.bar(
                user_goals,
                x='Goal Name',
                y=['Current Savings', 'Target Amount'],
                title='Goal Progress',
                barmode='overlay',
                color_discrete_map={'Current Savings': 'blue', 'Target Amount': 'lightgrey'}
            )
            st.plotly_chart(fig)
            
            # Create timeline chart
            goals_with_dates = user_goals.copy()
            goals_with_dates['Target Date'] = pd.to_datetime(goals_with_dates['Target Date'])
            goals_with_dates['Start Date'] = pd.to_datetime(goals_with_dates['Start Date'])
            goals_with_dates = goals_with_dates.sort_values('Target Date')
            
            # Calculate days from now to target
            today = pd.Timestamp.now()
            goals_with_dates['Days Remaining'] = (goals_with_dates['Target Date'] - today).dt.days
            
            fig = px.timeline(
                goals_with_dates,
                x_start='Start Date',
                x_end='Target Date',
                y='Goal Name',
                color='Progress %',
                color_continuous_scale='blues',
                title='Goal Timeline',
                labels={'Progress %': 'Progress (%)'}
            )
            
            # Update layout for better display
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig)

def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(
        page_title="Personal Finance Manager",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Create sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a page",
        ["Home", "Chat with Advisor", "Financial Nudges", "Goal Planning", "Data Visualization"]
    )
    
    # Show selected page
    if page == "Home":
        home_page()
    elif page == "Chat with Advisor":
        chatbot_page()
    elif page == "Financial Nudges":
        nudges_page()
    elif page == "Goal Planning":
        goal_planning_page()
    elif page == "Data Visualization":
        data_visualization_page()

if __name__ == "__main__":
    main()
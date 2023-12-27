import streamlit as st
from bokeh.plotting import figure
from bokeh.models import HoverTool, WheelZoomTool, ColumnDataSource
from datetime import timedelta, datetime
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
st.set_option('deprecation.showPyplotGlobalUse', False)
# Sidebar options
selected_period = st.sidebar.selectbox('Select Graph Period:', ['Weekly', 'Monthly', 'Quarterly', 'Annual'])
selected_plot_type = st.sidebar.selectbox('Select Plot Type:', ['Significant Drops', 'Differences', 'Correlation and Scatter'])

end = datetime.now().date()

# Subtract 20 years
start = end - timedelta(days=365.25 * 20)

# Function to load data based on the selected type
def load_data(selected_type):
    if selected_type == 'Financial Data':
        ticker = "AAPL"  # Example financial data (Apple Inc.)
    elif selected_type == 'Real Estate Data':
        ticker = "XLRE"  # Real Estate data
    elif selected_type == 'S&P 500 Index':
        ticker = "^GSPC"  # S&P 500 Index
    else:
        raise ValueError(f"Unsupported data type: {selected_type}")

    data = yf.download(ticker, start=start, end=end, progress=False)
    data.reset_index(inplace=True)
    data['Date'] = pd.to_datetime(data['Date'])
    return data

# Function to identify significant drops
def identify_significant_drops(data, period, thresholds):
    data = data.sort_values(by='Date')

    if period == 'Weekly':
        data['Group'] = data['Date'].dt.strftime('%G-%V')
    elif period == 'Monthly':
        data['Group'] = data['Date'].dt.to_period('M')
    elif period == 'Quarterly':
        data['Group'] = data['Date'].dt.to_period('Q')
    elif period == 'Annual':
        data['Group'] = data['Date'].dt.to_period('Y')
    else:
        raise ValueError(f"Unsupported period: {period}")

    max_values = data.groupby('Group')['Close'].max().reset_index()
    min_values = data.groupby('Group')['Close'].min().reset_index()

    mean_values = data.groupby('Group')['Close'].mean().reset_index()
    mean_values['Percentage_Drop'] = mean_values['Close'].pct_change() * 100

    significant_drops = []

    for threshold in thresholds:
        drop_points = mean_values[mean_values['Percentage_Drop'] < -threshold]
        significant_drops.append({'Threshold': threshold, 'Drop_Points': drop_points})

    return mean_values, max_values, min_values, significant_drops

# Calculate differences between max of one period and min of its succeeding period
def calculate_differences(max_values, min_values, period):
    max_values['Group'] = max_values['Group'].astype(str).sort_values()
    min_values['Group'] = min_values['Group'].astype(str).sort_values()

    differences = max_values['Close'] - min_values['Close'].shift(-1)
    differences = differences.to_frame(name='Difference')
    differences['Group'] = max_values['Group']
    
    return differences

# Function to create Bokeh plot for differences
def create_bokeh_plot_diff(data_mean, data_diff, period):
    data_diff['Group'] = data_diff['Group'].astype(str).sort_values()

    # Create a Bokeh figure
    p = figure(title=f'{period} Differences Between Maximum and Minimum Close Values Over Time',
               x_axis_label='Group', y_axis_label='Close Difference', x_range=data_diff['Group'], height=400)

    # Plot differences in blue
    source_diff = ColumnDataSource(data_diff)
    line_diff = p.line(x='Group', y='Difference', line_width=2, line_color='blue', source=source_diff, legend_label=f'{period} Differences')

    # Customize the plot appearance
    p.xaxis.major_label_orientation = 45  # Rotate x-axis labels
    p.legend.location = 'top_left'

    # Add HoverTool with custom tooltips for the line glyph
    hover = HoverTool(renderers=[line_diff], tooltips=[
        ('Group', '@Group'),
        ('Difference', '@Difference'),
    ])

    # Enable zoom tools
    p.add_tools(hover)
    p.add_tools(WheelZoomTool())

    return p

# Function to create Bokeh plot for significant drops
def create_bokeh_plot_drops(data_mean, data_drops, period):
    data_d = data_drops[0]['Drop_Points']
    data_mean['Group'] = data_mean['Group'].astype(str).sort_values()
    data_d['Group'] = data_d['Group'].astype(str).sort_values()

    # Create a Bokeh figure
    p = figure(title=f'{period} Mean Close Values Over Time with Significant Drops Highlighted',
               x_axis_label=period, y_axis_label='Close', x_range=data_mean['Group'], height=400)

    # Plot mean close values
    source_mean = ColumnDataSource(data_mean)
    line = p.line(x='Group', y='Close', line_width=2, source=source_mean, legend_label=f'{period} Mean Close')

    # Scatter significant drops in red
    source_drops = ColumnDataSource(data_d)
    circle = p.circle(x='Group', y='Close', size=8, color='red', source=source_drops, legend_label='Significant Drops', name='type')

    # Customize the plot appearance
    p.xaxis.major_label_orientation = 45  # Rotate x-axis labels
    p.legend.location = 'top_left'

    # Add HoverTool with custom tooltips for both line and circle glyphs
    hover = HoverTool(renderers=[line, circle], tooltips=[
        (period, '@Group'),
        ('Close', '@Close'),
        ('Type', '@type'),  # Add any other custom field you want to display
    ])

    # Enable zoom tools
    p.add_tools(hover)
    p.add_tools(WheelZoomTool())

    return p

# Load data based on the selected type
selected_type = st.sidebar.selectbox('Select Data Type:', ['Financial Data', 'Real Estate Data', 'S&P 500 Index'])
data = load_data(selected_type)

# Define the thresholds for significant drops
thresholds = [3, 5, 10, 15, 20]

# Perform the analysis for each time period
weekly_mean, weekly_max, weekly_min, weekly_drops = identify_significant_drops(data, 'Weekly', thresholds)
monthly_mean, monthly_max, monthly_min, monthly_drops = identify_significant_drops(data, 'Monthly', thresholds)
quarterly_mean, quarterly_max, quarterly_min, quarterly_drops = identify_significant_drops(data, 'Quarterly', thresholds)
annual_mean, annual_max, annual_min, annual_drops = identify_significant_drops(data, 'Annual', thresholds)

# Calculate differences between max of one period and min of its succeeding period
weekly_diff = calculate_differences(weekly_max, weekly_min, 'Weekly')
monthly_diff = calculate_differences(monthly_max, monthly_min, 'Monthly')
quarterly_diff = calculate_differences(quarterly_max, quarterly_min, 'Quarterly')
annual_diff = calculate_differences(annual_max, annual_min, 'Annual')

# Create Bokeh plots
weekly_plot_drops = create_bokeh_plot_drops(weekly_mean, weekly_drops, 'Weekly')
monthly_plot_drops = create_bokeh_plot_drops(monthly_mean, monthly_drops, 'Monthly')
quarterly_plot_drops = create_bokeh_plot_drops(quarterly_mean, quarterly_drops, 'Quarterly')
annual_plot_drops = create_bokeh_plot_drops(annual_mean, annual_drops, 'Annual')

weekly_diff_info = pd.DataFrame({
    'Group': weekly_diff['Group'],
    'Difference': weekly_diff['Difference']
})
monthly_diff_info = pd.DataFrame({
    'Group': monthly_diff['Group'],
    'Difference': monthly_diff['Difference']
})
quarterly_diff_info = pd.DataFrame({
    'Group': quarterly_diff['Group'],
    'Difference': quarterly_diff['Difference']
})
annual_diff_info = pd.DataFrame({
    'Group': annual_diff['Group'],
    'Difference': annual_diff['Difference']
})

weekly_plot_diff = create_bokeh_plot_diff(weekly_mean, weekly_diff_info, 'Weekly')
monthly_plot_diff = create_bokeh_plot_diff(monthly_mean, monthly_diff_info, 'Monthly')
quarterly_plot_diff = create_bokeh_plot_diff(quarterly_mean, quarterly_diff_info, 'Quarterly')
annual_plot_diff = create_bokeh_plot_diff(annual_mean, annual_diff_info, 'Annual')

# Get selected data based on sidebar options
# Get selected data based on sidebar options
def get_selected_data(period, plot_type):
    if period == 'Weekly':
        data_mean, data_max, data_min, data_drops = weekly_mean, weekly_max, weekly_min, weekly_drops
        data_diff_info = weekly_diff_info
    elif period == 'Monthly':
        data_mean, data_max, data_min, data_drops = monthly_mean, monthly_max, monthly_min, monthly_drops
        data_diff_info = monthly_diff_info
    elif period == 'Quarterly':
        data_mean, data_max, data_min, data_drops = quarterly_mean, quarterly_max, quarterly_min, quarterly_drops
        data_diff_info = quarterly_diff_info
    elif period == 'Annual':
        data_mean, data_max, data_min, data_drops = annual_mean, annual_max, annual_min, annual_drops
        data_diff_info = annual_diff_info
    else:
        raise ValueError(f"Unsupported period: {period}")

    if plot_type == 'Significant Drops':
        return data_mean, data_drops
    elif plot_type == 'Differences':
        return data_mean, data_diff_info
    elif plot_type == 'Correlation and Scatter':
        return data, None  # Return data without additional information for scatter plot and correlation
    else:
        raise ValueError(f"Unsupported plot type: {plot_type}")


# Create Bokeh plot based on selected data
selected_data_mean, selected_data_plot = get_selected_data(selected_period, selected_plot_type)

# Create Bokeh plot based on selected data
if selected_plot_type == 'Significant Drops':
    plot = create_bokeh_plot_drops(selected_data_mean, selected_data_plot, selected_period)
elif selected_plot_type == 'Differences':
    plot = create_bokeh_plot_diff(selected_data_mean, selected_data_plot, selected_period)
else:  # 'Correlation and Scatter' selected
    # Scatter plot and correlation for Financial Data and S&P 500 Index
    if selected_type == 'Financial Data':
        sp500_data = yf.download("^GSPC", start=start, end=end, progress=False)
        sp500_data.reset_index(inplace=True)
        sp500_data['Date'] = pd.to_datetime(sp500_data['Date'])
        fin_data = yf.download("XLK", start=start, end=end, progress=False)
        fin_data.reset_index(inplace=True)
        fin_data['Date'] = pd.to_datetime(fin_data['Date'])
        # Check length of financial data and S&P 500 data
        if len(fin_data) != len(sp500_data):
            st.warning("Length mismatch between Financial Data and S&P 500 Index. Correlation and Scatter plot may not be accurate.")

        # Scatter plot
        plt.scatter(fin_data['Close'], sp500_data['Close'])
        plt.xlabel("Financial Data")
        plt.ylabel("S$P 500 Data")
        plt.title("Scatter plot of Financial Data vs S$P500 Data")
        scatter_plot = plt.gcf()  

        # Correlation
        correlation = fin_data['Close'].corr(sp500_data['Close'])
        st.write(f"Correlation between Financial Data and S&P 500 Index: {correlation}")

    # Scatter plot and correlation for Real Estate Data and S&P 500 Index
    elif selected_type == 'Real Estate Data':
        # Assuming Real is your real estate dataframe
        Real = yf.download("XLRE", start=start, end=end, progress=False)
        Real.reset_index(inplace=True)
        Real['Date'] = pd.to_datetime(Real['Date'])
        sp500_data = yf.download("^GSPC", start=start, end=end, progress=False)
        sp500_data.reset_index(inplace=True)
        sp500_data['Date'] = pd.to_datetime(sp500_data['Date'])

        # Check length of Real Estate data and S&P 500 data
        if len(Real) != len(sp500_data):
            #st.warning("Length mismatch between Real Estate Data and S&P 500 Index. Correlation and Scatter plot may not be accurate.")
            i=sp500_data[sp500_data['Date']==Real['Date'][0]].index[0]
        # Scatter plot
            plt.scatter(Real["Close"], sp500_data['Close'].iloc[i:])
            plt.xlabel("Real Estate Data")
            plt.ylabel("S$P 500 Data")
            plt.title("Scatter plot of Real Estate Data vs S$P500 Data")
            scatter_plot = plt.gcf()  


        # Correlation
            arm = sp500_data['Close'].iloc[i:]
            arm = arm.reset_index().drop('index', axis=1)
            correlation = Real['Close'].corr(arm['Close'])
            st.write(f"Correlation between Real Estate Data and S&P 500 Index: {correlation}")
  
    else:
        st.warning("Correlation and Scatter plot are supported only for 'Financial Data' and 'Real Estate Data'.")

# Display the selected plots using Streamlit
st.title('Financial Data Analysis')
st.header('Significant Drops Analysis')
st.subheader('Select Data Type:')
st.write(f"Selected Data Type: {selected_type}")

# Display Bokeh plot
if selected_plot_type in ['Significant Drops', 'Differences']:
    st.subheader(f'{selected_period} Analysis - {selected_plot_type}')
    st.bokeh_chart(plot, use_container_width=True)
elif selected_plot_type == 'Correlation and Scatter':
    st.subheader(f'{selected_plot_type}')
    st.pyplot(scatter_plot, use_container_width=True)

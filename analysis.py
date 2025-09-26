import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats


def load_data(file_path: str) -> pd.DataFrame:
    """
    Load the Airbnb NYC 2019 dataset and perform basic cleaning:

    * Convert the `last_review` column to datetime.
    * Replace missing values in `reviews_per_month` with 0 (since no reviews implies zero months between reviews).
    * Drop rows with missing `neighbourhood_group` or `room_type` as these are essential categorical variables.

    Parameters
    ----------
    file_path : str
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame.
    """
    df = pd.read_csv(file_path)

    # Convert last_review to datetime, coerce errors to NaT
    df['last_review'] = pd.to_datetime(df['last_review'], errors='coerce')

    # Fill missing reviews_per_month with 0
    df['reviews_per_month'] = df['reviews_per_month'].fillna(0)

    # Drop rows with missing neighbourhood_group or room_type
    df = df.dropna(subset=['neighbourhood_group', 'room_type'])
    
    return df


def remove_price_outliers(df: pd.DataFrame, price_col: str = 'price') -> pd.DataFrame:
    """
    Remove extreme outliers from the price column using the IQR method.

    Outliers are defined as values below Q1 - 1.5*IQR or above Q3 + 1.5*IQR.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    price_col : str, optional
        Column name for price. Default is 'price'.

    Returns
    -------
    pd.DataFrame
        DataFrame with outliers removed.
    """
    q1 = df[price_col].quantile(0.25)
    q3 = df[price_col].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    filtered_df = df[(df[price_col] >= lower_bound) & (df[price_col] <= upper_bound)].copy()
    return filtered_df


def normalize_and_discretize(df: pd.DataFrame, price_col: str = 'price') -> pd.DataFrame:
    """
    Add normalized and discretized versions of the price column.

    * `price_zscore`: z-score normalization of price.
    * `price_bin`: discretize price into three bins (low, medium, high) based on quantiles.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    price_col : str, optional
        Column name for price. Default is 'price'.

    Returns
    -------
    pd.DataFrame
        DataFrame with additional columns.
    """
    mean = df[price_col].mean()
    std = df[price_col].std(ddof=0)
    df['price_zscore'] = (df[price_col] - mean) / std

    # Discretize price into tertiles
    df['price_bin'] = pd.qcut(df[price_col], q=3, labels=['low', 'medium', 'high'])
    return df


def descriptive_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute descriptive statistics for numeric columns.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    Returns
    -------
    pd.DataFrame
        Summary statistics.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    return df[numeric_cols].describe().T


def plot_price_distribution(df: pd.DataFrame, output_dir: str) -> None:
    """
    Create and save histogram and boxplot for price distribution.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    output_dir : str
        Directory path to save the figures.
    """
    sns.set(style="whitegrid")

    # Histogram
    plt.figure(figsize=(8, 5))
    sns.histplot(df['price'], kde=True, bins=50, color='skyblue')
    plt.title('Distribution of Airbnb Prices')
    plt.xlabel('Price (USD)')
    plt.ylabel('Count')
    plt.tight_layout()
    hist_path = f"{output_dir}/price_histogram.png"
    plt.savefig(hist_path)
    plt.close()

    # Boxplot by neighbourhood group
    plt.figure(figsize=(8, 5))
    sns.boxplot(x='neighbourhood_group', y='price', data=df, palette='Set2')
    plt.title('Price Distribution by Neighbourhood Group')
    plt.xlabel('Neighbourhood Group')
    plt.ylabel('Price (USD)')
    plt.tight_layout()
    box_path = f"{output_dir}/price_boxplot.png"
    plt.savefig(box_path)
    plt.close()


def plot_price_by_room_and_group(df: pd.DataFrame, output_dir: str) -> None:
    """
    Create and save bar plots showing average price by neighbourhood group and room type.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    output_dir : str
        Directory path to save the figures.
    """
    sns.set(style="whitegrid")
    plt.figure(figsize=(10, 6))
    avg_price = df.groupby(['neighbourhood_group', 'room_type'])['price'].mean().reset_index()
    sns.barplot(data=avg_price, x='neighbourhood_group', y='price', hue='room_type', palette='muted')
    plt.title('Average Price by Neighbourhood Group and Room Type')
    plt.xlabel('Neighbourhood Group')
    plt.ylabel('Average Price (USD)')
    plt.legend(title='Room Type')
    plt.tight_layout()
    bar_path = f"{output_dir}/avg_price_barplot.png"
    plt.savefig(bar_path)
    plt.close()


def anova_test(df: pd.DataFrame) -> tuple:
    """
    Perform a one-way ANOVA to test if mean prices differ across neighbourhood groups.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    Returns
    -------
    tuple
        F-statistic and p-value of the ANOVA test.
    """
    groups = [group['price'].values for name, group in df.groupby('neighbourhood_group')]
    f_stat, p_val = stats.f_oneway(*groups)
    return f_stat, p_val


def main():
    import os
    # File and output paths
    # Compute the absolute path to the dataset relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, '..', 'AB_NYC_2019.csv')
    output_dir = os.path.join(script_dir, 'figures')
    os.makedirs(output_dir, exist_ok=True)

    # Load and clean data
    df = load_data(csv_path)

    # Remove price outliers
    df = remove_price_outliers(df)

    # Normalize and discretize
    df = normalize_and_discretize(df)

    # Save descriptive statistics
    summary_stats = descriptive_statistics(df)
    summary_stats.to_csv('summary_statistics.csv')

    # Generate plots
    plot_price_distribution(df, output_dir)
    plot_price_by_room_and_group(df, output_dir)

    # Perform ANOVA
    f_stat, p_val = anova_test(df)
    with open('anova_results.txt', 'w') as f:
        f.write(f"One-way ANOVA results for price by neighbourhood_group\n")
        f.write(f"F-statistic: {f_stat:.3f}\n")
        f.write(f"p-value: {p_val:.5f}\n")

    print('Analysis complete. Results saved to output files.')


if __name__ == '__main__':
    main()
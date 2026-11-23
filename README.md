
# Order Fulfilment Delay & Cancellation Analysis

## Project Overview
An independent Business Analyst portfolio project analysing historical e-commerce order data from the public Olist Brazilian E-Commerce Dataset.

The project examines order fulfilment performance, delivery delays, cancellations and customer review patterns to identify areas for potential process improvement.

## Project Objectives
- Analyse order statuses and fulfilment performance.
- Measure late-delivery and cancellation patterns.
- Examine delivery performance across product categories and sellers.
- Explore the relationship between delivery delays and customer review scores.
- Propose business requirements and process improvements based on the findings.

## Tools & Technologies
- **Python:** Data validation and analysis
- **MySQL:** Data querying and analysis
- **Power BI:** Interactive dashboard and visualisation
- **Documentation:** BRD, user stories, acceptance criteria and process flows

## Key Findings
- Analysed **99,441 orders** from the public dataset.
- Identified a **6.77% late-delivery rate** among eligible delivered orders.
- Found a combined cancellation and unavailability rate of **1.24%**.
- The Audio category had the highest late-delivery rate at **11.78%**, among categories with at least 100 eligible orders.
- Late-delivered orders had an average review score of **2.27**, compared with **4.29** for on-time orders.

These findings show an association between delivery delays and lower customer ratings; they do not establish causation.

## Project Deliverables
- Python analysis script
- MySQL analysis queries
- Interactive Power BI dashboard
- Business Requirements Document (BRD)
- As-Is and To-Be process flows
- User stories and acceptance criteria
- Findings and recommendations summary

## Business Recommendations
Based on the historical patterns identified, the project proposes:
- Proactive alerts for potentially delayed orders.
- Clearer order-status updates.
- Seller performance monitoring.
- Improved visibility into fulfilment progress.

These are proposed improvements, not verified root causes of the historical delays.

## Dataset
**Source:** Olist Brazilian E-Commerce Dataset (Kaggle)

The dataset contains historical marketplace data. Raw CSV files are not included in this repository; users can obtain them from the original public source.

Dataset link: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

## Power BI Dashboard
The Power BI dashboard is available under the repository's **Releases** section.

Download: `Order_Fulfilment_Dashboard.pbix`

## Project Scope Note
This is an independent portfolio project using publicly available historical data. The analysis does not represent the actual operations of a company or retailer. Proposed business improvements are based on observed patterns and would require further stakeholder validation before implementation.

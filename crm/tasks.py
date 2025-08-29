import datetime
from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

@shared_task
def generate_crm_report():
    # GraphQL client setup
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=False,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # GraphQL query
    query = gql("""
    query {
      allCustomers {
        totalCount
      }
      allOrders {
        totalCount
        edges {
          node {
            totalAmount
          }
        }
      }
    }
    """)

    result = client.execute(query)

    total_customers = result["allCustomers"]["totalCount"]
    total_orders = result["allOrders"]["totalCount"]

    # Sum revenue from order edges
    revenue = sum(
        float(order["node"]["totalAmount"]) 
        for order in result["allOrders"]["edges"]
    )

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{timestamp} - Report: {total_customers} customers, {total_orders} orders, {revenue} revenue\n"

    with open("/tmp/crm_report_log.txt", "a") as f:
        f.write(log_line)

    print("CRM weekly report generated!")

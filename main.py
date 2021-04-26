import dataclasses
import datetime
import json
from collections import defaultdict
from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np
from dateutil import relativedelta


def difference_in_months(from_date: datetime.datetime, to_date: datetime.datetime):
    if from_date > to_date:
        from_date, to_date = to_date, from_date
    if from_date.year == to_date.year:
        return to_date.month - from_date.month

    # If there are any full years between, add 12 months for each year
    result = (to_date.year - from_date.year - 1) * 12
    # Add months for first year
    result += 12 - from_date.month
    # Add months for last year
    result += to_date.month

    return result


def group_transactions(transactions):
    first_date = datetime.datetime.fromtimestamp(transactions[0].PurchaseDate // 1000)
    last_date = datetime.datetime.fromtimestamp(transactions[-1].PurchaseDate // 1000)

    first_week_start = first_date - datetime.timedelta(days=first_date.weekday())
    last_week_start = last_date - datetime.timedelta(days=last_date.weekday())

    first_month_start = first_date - datetime.timedelta(days=first_date.day - 1)

    first_year_start = first_date.replace(month=1, day=1, hour=0, minute=0, second=0)

    num_weeks = (last_week_start - first_week_start).days // 7 + 1
    num_months = difference_in_months(first_date, last_date) + 1
    num_years = last_date.year - first_date.year + 1

    weekly_dates = np.array(
        [(first_week_start + datetime.timedelta(weeks=i)).replace(hour=0, minute=0, second=0) for i in
         range(num_weeks)],
        dtype=datetime.datetime)
    monthly_dates = np.array(
        [(first_month_start + relativedelta.relativedelta(months=i)).replace(hour=0, minute=0, second=0) for i in
         range(num_months)],
        dtype=datetime.datetime)
    yearly_dates = np.array([first_year_start + relativedelta.relativedelta(years=i) for i in range(num_years)],
                            dtype=datetime.datetime)

    weeks = defaultdict(list)
    months = defaultdict(list)
    years = defaultdict(list)

    for transaction in transactions:
        date = datetime.datetime.fromtimestamp(transaction.PurchaseDate // 1000)
        week_index = ((date - datetime.timedelta(days=date.weekday())) - first_week_start).days // 7

        month_index = difference_in_months(first_date, date)

        year_index = date.year - first_year_start.year

        weeks[weekly_dates[week_index]] += [transaction]
        months[monthly_dates[month_index]] += [transaction]
        years[yearly_dates[year_index]] += [transaction]

    return weeks, months, years


def plot(weekly_dates, weekly_amounts, monthly_dates, monthly_amounts):
    fig, ax = plt.subplots(2, 1)
    ax[0].step(weekly_dates, weekly_amounts, ".-", where="post")
    ax[0].set_title("Per week")
    ax[1].step(monthly_dates, monthly_amounts, ".-", where="post")
    ax[1].set_title("Per month")
    fig.suptitle("Spendings at Rema 1000 - from Æ")
    plt.grid(True)
    plt.show()


@dataclasses.dataclass(eq=True, frozen=True)
class Product:
    code: int
    text: str = dataclasses.field(compare=False)
    description: str = dataclasses.field(compare=False)
    group_code: int = dataclasses.field(compare=False)
    group_description: str = dataclasses.field(compare=False)
    volume: float = dataclasses.field(compare=False)
    amount: float = dataclasses.field(compare=False)

    @staticmethod
    def from_receipt(receipt):
        return Product(receipt.ProductCode if receipt.ProductCode is not None else 0,
                       receipt.Prodtxt1 if receipt.Prodtxt1 is not None else "Unknown",
                       receipt.ProductDescription if receipt.ProductDescription is not None else "Unknown",
                       receipt.ProductGroupCode if receipt.ProductGroupCode is not None else "Unknown",
                       receipt.ProductGroupDescription if receipt.ProductGroupDescription is not None else "Unknown",
                       receipt.Volume,
                       receipt.Amount)


def process_receipts(transactions):
    items = defaultdict(lambda: {'count': 0, 'total': 0})
    for transaction in transactions:
        for receipt in transaction.Receipt:
            product = Product.from_receipt(receipt)
            items[product]['total'] += receipt.Amount
            items[product]['count'] += 1
    return items


def plot_top_n_products(title, products, n):
    if (len(products) < 2):
        print(f"{title} has unknown products worth kr {[v for v in products.values()][0]['total']:.2f} ,-")
        return
    keys = []
    values = []
    total = sum(map(lambda x: x['total'], (v for v in products.values())))
    unknown = 0
    for key, value in sorted(products.items(), key=lambda x: x[1]['total'], reverse=True):
        if key.code != 0:
            keys.append(key)
            values.append(value)
        else:
            unknown = value['total']

    _slice = slice(0, n, None)
    fig, ax = plt.subplots(1, 1)
    fig.suptitle(f"{title} - kr {total:.2f},-")
    ax.set_title(f"Ukjent: kr {unknown:.2f},-")
    bottom = list(map(lambda x: x.text, keys[_slice]))
    width = list(map(lambda x: x['total'], values[_slice]))
    ax.barh(bottom, width, color='lightblue')
    plt.subplots_adjust(left=0.4)
    for i, (k, v) in enumerate(zip(keys[_slice], values[_slice])):
        ax.text(2, i, f"{k.amount:<7.2f} * {v['count']:>2.0f} = {v['total']:.2f}", va='center', color='black',
                alpha=0.7)


def plot_top_n_periodically(title_generator, periods, n):
    for period, transactions in periods.items():
        products = process_receipts(transactions)
        plot_top_n_products(title_generator(period), products, n)


def main(filename, n):
    with open(filename) as json_file:
        # Parse JSON into an object with attributes corresponding to dict keys.
        x = json.load(json_file, object_hook=lambda d: SimpleNamespace(**d))

    # process_transactions(x.TransactionsInfo.Transactions)
    weeks, months, years = group_transactions(x.TransactionsInfo.Transactions)

    plot_top_n_periodically(lambda x: x.strftime("%B %Y"), months, n)
    plot_top_n_periodically(lambda x: x.strftime("%Y"), years, n)

    plt.show()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str)
    parser.add_argument("--n", type=int, default=20)

    args = parser.parse_args()

    main(args.filename, args.n)
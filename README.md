# rema-parser

The norwegian grocery store Rema 1000 offers to export a detailed transaction history to a JSON file. This is done through their app "Æ", through `Profile` - 
`Vilkår og samtykke` - `Se dine data` - `Få tilsendt data i maskinlesbart format`. The file acts as input to the script

The simple script organises the transaction by week, month and year, and plots the top n (default 20) products for the each month and year. The detailed transaction
history is only available if your payment information is confirmed in their app, "Æ". It becomes available for purchases made subsequent to confirming the payment 
information.

# Installation
Install [poetry](https://python-poetry.org) then run 

```bash
poetry install
poetry run python main.py <filename> [--n <plot top n products>]
```



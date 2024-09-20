#!/usr/bin/python

from __future__ import print_function

#!/usr/bin/python

from __future__ import print_function
import os
import math
import numpy_financial as npf
import locale
import argparse
import sys

pretty = True
set_verbose_level = 1

def log_print(verbose_level, format_str, tuple_of_args=()):
    if set_verbose_level >= verbose_level:
        print(format_str % tuple_of_args)

class Fl_fmt:
    locale_set = 0
    locale_avail = 0

    def __init__(self, f):
        if not Fl_fmt.locale_set:
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.utf8')
                Fl_fmt.locale_avail = 1
            except:
                pass
            Fl_fmt.locale_set = 1
        self.f = f

    def __str__(self):
        if Fl_fmt.locale_avail:
            return locale.format("%.2f", self.f, grouping=pretty)
        else:
            return "%.2f" % self.f

def validate_value(low, high, given, mem_type, default):
    '''
        low/high: range
        given: user input as string
        memtype: 0: float, 1: int, 2/anything-else: string
        default: if range-check fails supply back this value. Note: string has no range check. Returned as-is.
    '''
    if mem_type == 1:
        val = int(given)
    elif mem_type == 0:
        val = float(given)
    else:
        return given
    if val < low or val > high:  # Fixed condition
        print("You should enter a value between %d and %d. You gave %s" % (low, high, given))
        return default
    else:
        return val

inputs = [
    ["home_val", "Home Value", "300000", 100000, 1000000, 1],
    ["how_long", "How long do you plan to hold the home", "20", 2, 100, 1],
    ["mort_per", "Mortgage percent", "3", 1.0, 25.0, 0],
    ["down_pay", "Down Payment %", "0", 1, 100, 1],
    ["mort_ins", "Mortgage insurance %", "0.5", 0.3, 1.2, 0],
    ["mort_term", "Mortgage Term", "30", 2, 40, 1],
    ["price_appr", "Price Appreciation %", "6.0", 1.0, 25.0, 0],
    ["rent_appr", "Rent Appreciation%", "4.5", 1.0, 25.0, 0],
    ["inflation", "Inflation %", "4.2", 1.0, 25.0, 0],
    ["inv_rate", "Investment Rate%", "12.0", 1.0, 25.0, 0],
    ["prop_tax", "Property Tax%", "1.1", 0.1, 10.0, 0],
    ["joint", "Joint", "yes", "yes", "no", 2],
    ["marg_rate", "Marginal Rate%", "22", 0, 25.0, 0],
    ["buy_loss", "Buying loss%", "1.5", 0, 25.0, 0],
    ["sell_loss", "Selling loss%", "6", 0, 25.0, 0],
    ["maint", "Maintenance", ".5", 0.1, 10.0, 0],
    ["own_ins", "Owner Insurance", "0.46", 0.1, 10.0, 0],
    ["month_comm", "Monthly Common", "250", 0, 5000, 1],
    ["rent_ins", "Renter Insurance", "0.5", 0.1, 10.0, 0],
]

def parse_command_line_inputs():
    parser = argparse.ArgumentParser()
    for i in inputs:
        option = "--" + i[0]
        parser.add_argument(option, dest=i[0], help=i[1], default=i[2])
    parser.add_argument("--nopretty", action="store_true")
    parser.add_argument("-l", "--log_level", type=int)

    parsed_args = parser.parse_args()
    failed = False
    given_inputs = {}
    for i in inputs:
        if not hasattr(parsed_args, i[0]):
            print("Supply input: %s" % i[0])
            failed = True
        else:
            given = getattr(parsed_args, i[0])
            def_val = i[2]
            low = i[3]
            high = i[4]
            mem_type = i[5]
            value = validate_value(low, high, given, mem_type, def_val)
            given_inputs[i[0]] = value

    if failed:
        sys.exit(1)

    global pretty
    if parsed_args.nopretty:
        pretty = False

    global set_verbose_level
    if parsed_args.log_level is not None:
        set_verbose_level = parsed_args.log_level
        if set_verbose_level == 0:
            pretty = False

    return given_inputs

def compound_interest(p, n, r):
    rr = r / 100.0
    return p * math.pow((1 + rr), n)

def extrapolate_values(initial, years, rate):
    val_i = initial
    rr = rate / 100.0
    result = []
    for i in range(years):
        val_i = val_i * (1 + rr)
        result.append(val_i)
    return result

def extrapolate_values_on_a_base(base, base_inc_rate, years, rate_on_base):
    base_i = base
    rr = base_inc_rate / 100.0
    vr = rate_on_base / 100.0
    result = []
    for i in range(years):
        base_i = base_i * (1 + rr)
        value_i = base_i * vr
        result.append(value_i)
    return result

def principal_remaining_after(p, n, r, rem_years):
    rr = r / 1200.0
    nn = n * 12
    rem_mths = rem_years * 12
    paid_mths = nn - rem_mths
    paid_prin = 0.0
    for i in range(1, paid_mths + 1):
        pp = npf.ppmt(rr, i, nn, p)
        paid_prin += pp
    return (p * -1) - paid_prin

def get_a_renter_oppurtunity_cost(rent_guess, how_long, rent_appr, rent_ins):
    rental_values = extrapolate_values(rent_guess * 12, how_long, rent_appr)
    renter_insur = extrapolate_values_on_a_base(rent_guess * 12, rent_appr, how_long, rent_ins)
    renter_oppurtunity_cost = 0.0
    renter_year_expense = []
    for i in range(inp['how_long']):
        renter_exp_for_this_year = rental_values[i] + renter_insur[i]
        renter_year_expense.append(renter_exp_for_this_year)
        years_left = inp['how_long'] - i
        renter_oppurtunity_cost += compound_interest(renter_exp_for_this_year, years_left, inp['inv_rate'])

    log_print(5, "Renter situation:")
    if set_verbose_level >= 5:
        for i in range(inp['how_long']):
            log_print(5, "year %d,  rent: %s rent_insur: %s net_yearly: %s",
                      (i, Fl_fmt(rental_values[i]), Fl_fmt(renter_insur[i]), Fl_fmt(renter_year_expense[i])))

    log_print(5, "oppurtunity_cost_for_renter at guess_rent:%s is: %s",
              (Fl_fmt(rent_guess), Fl_fmt(renter_oppurtunity_cost)))

    return renter_oppurtunity_cost

# Remaining code remains unchanged.

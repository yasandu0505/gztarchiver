def identify_input_kind(args):
    """Returns input kind string or 'invalid'."""
    if args.year and args.lang:
        if args.month and args.day:
            return "year-month-day-lang"
        elif args.month:
            return "year-month-lang"
        else:
            return "year-lang"
    else:
        return "invalid"

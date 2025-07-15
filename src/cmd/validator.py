def identify_input_kind(args):
    valid_langs = {"en", "si", "ta"}

    if not args.year or not args.lang:
        return "invalid-input"

    if args.lang not in valid_langs:
        return "invalid-lang-input"

    if args.month and args.day:
        return "year-month-day-lang"
    elif args.month:
        return "year-month-lang"
    else:
        return "year-lang"

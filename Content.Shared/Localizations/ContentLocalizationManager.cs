using System.Globalization;
using System.Linq;
using System.Text.RegularExpressions;
using System.Text;
using Content.Shared.IdentityManagement; // Sierra-Stories EDIT ADD
using Content.Shared.Stacks;
using Robust.Shared.Utility;

namespace Content.Shared.Localizations
{
    public sealed class ContentLocalizationManager
    {
        [Dependency] private readonly ILocalizationManager _loc = default!;

        // If you want to change your codebase's language, do it here.
        private const string Culture = "ru-RU"; // Sierra-Stories EDIT ADD Corvax-Localization
        private const string FallbackCulture = "en-US";  // Sierra-Stories EDIT ADD Corvax-Localization

        /// <summary>
        /// Custom format strings used for parsing and displaying minutes:seconds timespans.
        /// </summary>
        public static readonly string[] TimeSpanMinutesFormats = new[]
        {
            @"m\:ss",
            @"mm\:ss",
            @"%m",
            @"mm"
        };

        public void Initialize()
        {
            var culture = new CultureInfo(Culture);
            var fallbackCulture = new CultureInfo(FallbackCulture);  // Sierra-Stories EDIT ADD // Corvax-Localization

            _loc.LoadCulture(culture);
            _loc.LoadCulture(fallbackCulture);  // Sierra-Stories EDIT ADD // Corvax-Localization
            _loc.SetFallbackCluture(fallbackCulture);  // Sierra-Stories EDIT ADD Corvax-Localization
            _loc.AddFunction(culture, "MANY", FormatMany);  // Sierra-Stories EDIT ADD Corvax-Localization: To prevent problems in auto-generated locale files
            _loc.AddFunction(culture, "PRESSURE", FormatPressure);
            _loc.AddFunction(culture, "POWERWATTS", FormatPowerWatts);
            _loc.AddFunction(culture, "POWERJOULES", FormatPowerJoules);
            // NOTE: ENERGYWATTHOURS() still takes a value in joules, but formats as watt-hours.
            _loc.AddFunction(culture, "ENERGYWATTHOURS", FormatEnergyWattHours);
            _loc.AddFunction(culture, "UNITS", FormatUnits);
            _loc.AddFunction(culture, "TOSTRING", args => FormatToString(culture, args));
            _loc.AddFunction(culture, "LOC", FormatLoc);
            _loc.AddFunction(culture, "NATURALFIXED", FormatNaturalFixed);
            _loc.AddFunction(culture, "NATURALPERCENT", FormatNaturalPercent);
            _loc.AddFunction(culture, "PLAYTIME", FormatPlaytime);


            /*
             * The following language functions are specific to the english localization. When working on your own
             * localization you should NOT modify these, instead add new functions specific to your language/culture.
             * This ensures the english translations continue to work as expected when fallbacks are needed.
             */
            var cultureEn = new CultureInfo("en-US");

            _loc.AddFunction(cultureEn, "MAKEPLURAL", FormatMakePlural);
            _loc.AddFunction(cultureEn, "MANY", FormatMany);

            // RU DECLENT
            var cultureRu = new CultureInfo("ru-RU");
            _loc.AddFunction(cultureRu, "DECLINE_NOMINATIVE", FuncDeclineNominative);
            _loc.AddFunction(cultureRu, "DECLINE_GENITIVE", FuncDeclineGenitive);
            _loc.AddFunction(cultureRu, "DECLINE_DATIVE", FuncDeclineDative);
            _loc.AddFunction(cultureRu, "DECLINE_ACCUSATIVE", FuncDeclineAccusative);
            _loc.AddFunction(cultureRu, "DECLINE_INSTRUMENTAL", FuncDeclineInstrumental);
            _loc.AddFunction(cultureRu, "DECLINE_PREPOSITIONAL", FuncDeclinePrepositional);
            _loc.AddFunction(cultureRu, "DECLINE_NOMINATIVE_CAPITALIZE", FuncDeclineNominativeCapitalize);
            _loc.AddFunction(cultureRu, "DECLINE_GENITIVE_CAPITALIZE", FuncDeclineGenitiveCapitalize);
            _loc.AddFunction(cultureRu, "DECLINE_DATIVE_CAPITALIZE", FuncDeclineDativeCapitalize);
            _loc.AddFunction(cultureRu, "DECLINE_ACCUSATIVE_CAPITALIZE", FuncDeclineAccusativeCapitalize);
            _loc.AddFunction(cultureRu, "DECLINE_INSTRUMENTAL_CAPITALIZE", FuncDeclineInstrumentalCapitalize);
            _loc.AddFunction(cultureRu, "DECLINE_PREPOSITIONAL_CAPITALIZE", FuncDeclinePrepositionalCapitalize);
        }

        private ILocValue DeclensionHelper(LocArgs args, string target_case = "nominative", bool capitalize = false, int amount = 1)
        {
            if (args.Args.Count < 1)
            {
                return capitalize ? CapitalizeDeclent(args.Args[0]) : args.Args[0];
            }

            ILocValue entity0 = args.Args[0];
            if (entity0.Value is EntityUid entity)
            {
                var entityManager = IoCManager.Resolve<IEntityManager>();
                // .ftl supports only lowercase letters and - symbol
                // .toml ["captain's carapace"] -> .ftl captain-s-carapace
                var entityName = Identity.Name(entity, entityManager);
                entityName = ConvertToFTLKey(entityName);

                if (entityManager.TryGetComponent<StackComponent>(entity, out var stack))
                {
                    amount = stack.Count;
                }

                // one - 1, 21, 31...
                var number = (amount % 10 == 1 && amount % 100 != 11) ? "one" :
                // few - 2, 3, 4, 22, 23, 24...
                    amount % 10 >= 2 && amount % 10 <= 4 && (amount % 100 < 10 || amount % 100 >= 20) ? "few" :
                // many - 0, 5-20, 25-30, other...
                    "many";

                var loc = new LocValueString(Loc.GetString(entityName, ("case", target_case), ("number", number)));
                if (loc.Value.Contains(entityName))
                {
                    return capitalize ? CapitalizeDeclent(args.Args[0]) : args.Args[0];
                }
                return capitalize ? CapitalizeDeclent(loc) : loc;
            }
            return capitalize ? CapitalizeDeclent(args.Args[0]) : args.Args[0];
        }

        private ILocValue CapitalizeDeclent(ILocValue toCapitalize)
        {
            var input = toCapitalize.Format(new LocContext());
            if (!String.IsNullOrEmpty(input))
                return new LocValueString(input[0].ToString().ToUpper() + input.Substring(1));
            else return new LocValueString("");
        }


        private string ConvertToFTLKey(string entityName)
        {
            // .ftl only supports a-zA-Z and -
            // we will use onle lowercase
            entityName = entityName.ToLower();
            entityName = string.Concat(entityName.Select(c => char.IsLetterOrDigit(c) ? c : '-'));
            entityName = ConvertCyrillicToLatin(entityName);
            return entityName;
        }

        private static readonly Dictionary<char, string> CyrillicToLatinMap = new Dictionary<char, string>
        {
            {'а', "a"}, {'б', "b"}, {'в', "v"}, {'г', "g"}, {'д', "d"}, {'е', "e"},
            {'ё', "yo"}, {'ж', "zh"}, {'з', "z"}, {'и', "i"}, {'й', "y"}, {'к', "k"},
            {'л', "l"}, {'м', "m"}, {'н', "n"}, {'о', "o"}, {'п', "p"}, {'р', "r"},
            {'с', "s"}, {'т', "t"}, {'у', "u"}, {'ф', "f"}, {'х', "kh"}, {'ц', "ts"},
            {'ч', "ch"}, {'ш', "sh"}, {'щ', "shch"}, {'ъ', ""}, {'ы', "y"}, {'ь', ""},
            {'э', "e"}, {'ю', "yu"}, {'я', "ya"},
        };

        private string ConvertCyrillicToLatin(string checkme)
        {
            var input = checkme;
            if (string.IsNullOrEmpty(input))
                return checkme;

            var result = new StringBuilder();

            foreach (char c in input)
            {
                if (CyrillicToLatinMap.TryGetValue(c, out string? replacement))
                {
                    result.Append(replacement);
                }
                else
                {
                    result.Append(c);
                }
            }

            return result.ToString();
        }

        private ILocValue FuncDeclineNominative(LocArgs args)
        {
            return DeclensionHelper(args, "nominative");
        }

        private ILocValue FuncDeclineGenitive(LocArgs args)
        {
            return DeclensionHelper(args, "genitive");
        }

        private ILocValue FuncDeclineDative(LocArgs args)
        {
            return DeclensionHelper(args, "dative");
        }

        private ILocValue FuncDeclineAccusative(LocArgs args)
        {
            return DeclensionHelper(args, "accusative");
        }

        private ILocValue FuncDeclineInstrumental(LocArgs args)
        {
            return DeclensionHelper(args, "instrumental");
        }

        private ILocValue FuncDeclinePrepositional(LocArgs args)
        {
            return DeclensionHelper(args, "prepositional");
        }

        private ILocValue FuncDeclineNominativeCapitalize(LocArgs args)
        {
            return DeclensionHelper(args, "nominative", true);
        }

        private ILocValue FuncDeclineGenitiveCapitalize(LocArgs args)
        {
            return DeclensionHelper(args, "genitive", true);
        }

        private ILocValue FuncDeclineDativeCapitalize(LocArgs args)
        {
            return DeclensionHelper(args, "dative", true);
        }

        private ILocValue FuncDeclineAccusativeCapitalize(LocArgs args)
        {
            return DeclensionHelper(args, "accusative", true);
        }

        private ILocValue FuncDeclineInstrumentalCapitalize(LocArgs args)
        {
            return DeclensionHelper(args, "instrumental", true);
        }

        private ILocValue FuncDeclinePrepositionalCapitalize(LocArgs args)
        {
            return DeclensionHelper(args, "prepositional", true);
        }

        private ILocValue FormatMany(LocArgs args)
        {
            var count = ((LocValueNumber) args.Args[1]).Value;

            if (Math.Abs(count - 1) < 0.0001f)
            {
                return (LocValueString) args.Args[0];
            }
            else
            {
                return (LocValueString) FormatMakePlural(args);
            }
        }

        private ILocValue FormatNaturalPercent(LocArgs args)
        {
            var number = ((LocValueNumber) args.Args[0]).Value * 100;
            var maxDecimals = (int)Math.Floor(((LocValueNumber) args.Args[1]).Value);
            var formatter = (NumberFormatInfo)NumberFormatInfo.GetInstance(CultureInfo.GetCultureInfo(Culture)).Clone();
            formatter.NumberDecimalDigits = maxDecimals;
            return new LocValueString(string.Format(formatter, "{0:N}", number).TrimEnd('0').TrimEnd(char.Parse(formatter.NumberDecimalSeparator)) + "%");
        }

        private ILocValue FormatNaturalFixed(LocArgs args)
        {
            var number = ((LocValueNumber) args.Args[0]).Value;
            var maxDecimals = (int)Math.Floor(((LocValueNumber) args.Args[1]).Value);
            var formatter = (NumberFormatInfo)NumberFormatInfo.GetInstance(CultureInfo.GetCultureInfo(Culture)).Clone();
            formatter.NumberDecimalDigits = maxDecimals;
            return new LocValueString(string.Format(formatter, "{0:N}", number).TrimEnd('0').TrimEnd(char.Parse(formatter.NumberDecimalSeparator)));
        }

        private static readonly Regex PluralEsRule = new("^.*(s|sh|ch|x|z)$");

        private ILocValue FormatMakePlural(LocArgs args)
        {
            var text = ((LocValueString) args.Args[0]).Value;
            var split = text.Split(" ", 1);
            var firstWord = split[0];
            if (PluralEsRule.IsMatch(firstWord))
            {
                if (split.Length == 1)
                    return new LocValueString($"{firstWord}es");
                else
                    return new LocValueString($"{firstWord}es {split[1]}");
            }
            else
            {
                if (split.Length == 1)
                    return new LocValueString($"{firstWord}s");
                else
                    return new LocValueString($"{firstWord}s {split[1]}");
            }
        }

        // TODO: allow fluent to take in lists of strings so this can be a format function like it should be.
        /// <summary>
        /// Formats a list as per english grammar rules.
        /// </summary>
        public static string FormatList(List<string> list)
        {
            return list.Count switch
            {
                <= 0 => string.Empty,
                1 => list[0],
                2 => $"{list[0]} and {list[1]}",
                _ => $"{string.Join(", ", list.GetRange(0, list.Count - 1))}, and {list[^1]}"
            };
        }

        /// <summary>
        /// Formats a list as per english grammar rules, but uses or instead of and.
        /// </summary>
        public static string FormatListToOr(List<string> list)
        {
            return list.Count switch
            {
                <= 0 => string.Empty,
                1 => list[0],
                2 => $"{list[0]} or {list[1]}",
                _ => $"{string.Join(", ", list.GetRange(0, list.Count - 1))}, or {list[^1]}"
            };
        }

        /// <summary>
        /// Formats a direction struct as a human-readable string.
        /// </summary>
        public static string FormatDirection(Direction dir)
        {
            return Loc.GetString($"zzzz-fmt-direction-{dir.ToString()}");
        }

        /// <summary>
        /// Formats playtime as hours and minutes.
        /// </summary>
        public static string FormatPlaytime(TimeSpan time)
        {
            time = TimeSpan.FromMinutes(Math.Ceiling(time.TotalMinutes));
            var hours = (int)time.TotalHours;
            var minutes = time.Minutes;
            return Loc.GetString($"zzzz-fmt-playtime", ("hours", hours), ("minutes", minutes));
        }

        private static ILocValue FormatLoc(LocArgs args)
        {
            var id = ((LocValueString) args.Args[0]).Value;

            return new LocValueString(Loc.GetString(id, args.Options.Select(x => (x.Key, x.Value.Value!)).ToArray()));
        }

        private static ILocValue FormatToString(CultureInfo culture, LocArgs args)
        {
            var arg = args.Args[0];
            var fmt = ((LocValueString) args.Args[1]).Value;

            var obj = arg.Value;
            if (obj is IFormattable formattable)
                return new LocValueString(formattable.ToString(fmt, culture));

            return new LocValueString(obj?.ToString() ?? "");
        }

        private static ILocValue FormatUnitsGeneric(
            LocArgs args,
            string mode,
            Func<double, double>? transformValue = null)
        {
            const int maxPlaces = 5; // Matches amount in _lib.ftl
            var pressure = ((LocValueNumber) args.Args[0]).Value;

            if (transformValue != null)
                pressure = transformValue(pressure);

            var places = 0;
            while (pressure > 1000 && places < maxPlaces)
            {
                pressure /= 1000;
                places += 1;
            }

            return new LocValueString(Loc.GetString(mode, ("divided", pressure), ("places", places)));
        }

        private static ILocValue FormatPressure(LocArgs args)
        {
            return FormatUnitsGeneric(args, "zzzz-fmt-pressure");
        }

        private static ILocValue FormatPowerWatts(LocArgs args)
        {
            return FormatUnitsGeneric(args, "zzzz-fmt-power-watts");
        }

        private static ILocValue FormatPowerJoules(LocArgs args)
        {
            return FormatUnitsGeneric(args, "zzzz-fmt-power-joules");
        }

        private static ILocValue FormatEnergyWattHours(LocArgs args)
        {
            const double joulesToWattHours = 1.0 / 3600;

            return FormatUnitsGeneric(args, "zzzz-fmt-energy-watt-hours", joules => joules * joulesToWattHours);
        }

        private static ILocValue FormatUnits(LocArgs args)
        {
            if (!Units.Types.TryGetValue(((LocValueString) args.Args[0]).Value, out var ut))
                throw new ArgumentException($"Unknown unit type {((LocValueString) args.Args[0]).Value}");

            var fmtstr = ((LocValueString) args.Args[1]).Value;

            double max = Double.NegativeInfinity;
            var iargs = new double[args.Args.Count - 1];
            for (var i = 2; i < args.Args.Count; i++)
            {
                var n = ((LocValueNumber) args.Args[i]).Value;
                if (n > max)
                    max = n;

                iargs[i - 2] = n;
            }

            if (!ut.TryGetUnit(max, out var mu))
                throw new ArgumentException("Unit out of range for type");

            var fargs = new object[iargs.Length];

            for (var i = 0; i < iargs.Length; i++)
                fargs[i] = iargs[i] * mu.Factor;

            fargs[^1] = Loc.GetString($"units-{mu.Unit.ToLower()}");

            // Before anyone complains about "{"+"${...}", at least it's better than MS's approach...
            // https://docs.microsoft.com/en-us/dotnet/standard/base-types/composite-formatting#escaping-braces
            //
            // Note that the closing brace isn't replaced so that format specifiers can be applied.
            var res = String.Format(
                fmtstr.Replace("{UNIT", "{" + $"{fargs.Length - 1}"),
                fargs
            );

            return new LocValueString(res);
        }

        private static ILocValue FormatPlaytime(LocArgs args)
        {
            var time = TimeSpan.Zero;
            if (args.Args is { Count: > 0 } && args.Args[0].Value is TimeSpan timeArg)
            {
                time = timeArg;
            }
            return new LocValueString(FormatPlaytime(time));
        }
    }
}

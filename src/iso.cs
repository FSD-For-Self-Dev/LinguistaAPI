using System;
using System.Collections.Generic;
using System.Globalization;

namespace Languages
{
    class Program
    {
        public static void Main()
        {
            List<string> list = new List<string>();
            CultureInfo[] cultures = CultureInfo.GetCultures(CultureTypes.SpecificCultures);
            foreach (CultureInfo culture in cultures)
            {
                RegionInfo region = new RegionInfo(culture.Name);
                var text = string.Format("'{2}-{3}': {{\n\t'language': '{1}'\n\t'country': '{0}'\n\t'country_cca3': '{4}'\n}},",
                    region.EnglishName, culture.Parent.EnglishName,
                    culture.Parent.TwoLetterISOLanguageName,
                        region.TwoLetterISORegionName, region.ThreeLetterISORegionName);
                text = text.Replace("&", "&amp;");
                list.Add(text);
            }
            list.Sort();
            list.ForEach(Console.WriteLine);
        }
    }
}

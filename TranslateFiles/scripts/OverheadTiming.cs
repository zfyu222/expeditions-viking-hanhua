// Target the game's .NET 2.0 profile. No plugin or extra runtime DLL is needed.
public static class OverheadTiming
{
    public static float GetDisplaySeconds(float originalSeconds, string text)
    {
        int han = 0;
        bool inTag = false;
        for (int i = 0; i < text.Length; i++)
        {
            char c = text[i];
            if (c == '<') { inTag = true; continue; }
            if (c == '>') { inTag = false; continue; }
            if (!inTag && ((c >= '\u3400' && c <= '\u9fff') ||
                           (c >= '\uf900' && c <= '\ufaff'))) han++;
        }
        // Keep the original timer for Latin text and never shorten any timer.
        if (han == 0) return originalSeconds;
        return System.Math.Max(originalSeconds, System.Math.Max(3f, han * 0.2f));
    }
}

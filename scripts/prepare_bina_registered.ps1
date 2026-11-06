# Package the original drawing through an imagegen matte and registered masks.
# All visible colors come from the reference, with no independent part scaling.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$root = Split-Path $PSScriptRoot -Parent
$out = Join-Path $root 'assets/bina-live2d/source-registered'
function Write-Utf8Lf([string]$path, [string]$content) {
    [IO.File]::WriteAllText($path, ($content -replace "`r`n", "`n").TrimEnd() + "`n", [Text.UTF8Encoding]::new($false))
}
$source = Join-Path $root 'assets/bina-tpose/casual/bina-casual-tpose-front.png'
$measure = Get-Content (Join-Path $root 'assets/bina-tpose/measurements/proportions.json') -Raw | ConvertFrom-Json
$expected = $measure.views.'casual-front'.sha256
$actual = (Get-FileHash $source -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw 'Reference hash changed; review masks before packaging.' }
New-Item -ItemType Directory -Force (Join-Path $out 'parts') | Out-Null
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;

public sealed class RegisteredPart {
    public string name;
    public int left, top, width, height;
}
public static class BinaRegistered {
    static GraphicsPath Polygon(params float[] coords) {
        var points = new PointF[coords.Length/2];
        for(int i=0;i<points.Length;i++) points[i]=new PointF(coords[2*i],coords[2*i+1]);
        var path=new GraphicsPath(); path.AddPolygon(points); return path;
    }
    static bool Box(int x,int y,int l,int t,int r,int b) { return x>=l && x<r && y>=t && y<b; }
    static bool Iris(int x,int y,int cx) {
        double dx=(x-cx)/5.5, dy=(y-117)/6.0;
        return dx*dx+dy*dy<=1;
    }
    static bool[] ExteriorWhite(Bitmap src) {
        int w=src.Width,h=src.Height;
        var exterior=new bool[w*h]; var queue=new Queue<int>();
        for(int x=0;x<w;x++) { queue.Enqueue(x); queue.Enqueue((h-1)*w+x); }
        for(int y=0;y<h;y++) { queue.Enqueue(y*w); queue.Enqueue(y*w+w-1); }
        while(queue.Count>0) {
            int p=queue.Dequeue(); if(exterior[p]) continue;
            int x=p%w,y=p/w; Color c=src.GetPixel(x,y);
            int min=Math.Min(c.R,Math.Min(c.G,c.B)),max=Math.Max(c.R,Math.Max(c.G,c.B));
            if(min<225 || max-min>15) continue;
            exterior[p]=true;
            if(x>0)queue.Enqueue(p-1); if(x<w-1)queue.Enqueue(p+1);
            if(y>0)queue.Enqueue(p-w); if(y<h-1)queue.Enqueue(p+w);
        }
        return exterior;
    }
    public static long changedPixels;
    public static long sourceColorMismatches;
    public static RegisteredPart[] Build(string reference,string matteFile,string cleanFile,string output) {
        var names=new[]{"skin_underpaint","torso","sleeve_left","sleeve_right","hand_left","hand_right",
            "skirt","leg_left","leg_right","neck","face","back_hair","hair_left","hair_right","hair_front",
            "glasses","eye_left","eye_right","iris_left","iris_right","brow_left","brow_right","nose","mouth"};
        using(var src=new Bitmap(reference)) using(var matte=new Bitmap(matteFile)) using(var clean=new Bitmap(cleanFile))
        using(var face=Polygon(742,70,752,72,766,72,782,69,788,82,794,103,800,116,794,138,788,149,779,163,765,173,747,163,735,152,727,139,721,116,725,97,733,80))
        using(var cleanRegion=Polygon(739,66,782,66,793,90,799,119,790,147,765,171,737,153,724,122,728,92)) {
            int w=src.Width,h=src.Height;
            if(w!=1536||h!=1024||matte.Size!=src.Size||clean.Size!=src.Size)
                throw new Exception("All source images must share the unchanged 1536x1024 canvas.");
            bool[] exterior=ExteriorWhite(src);
            var layers=new Dictionary<string,Bitmap>();
            var bounds=new Dictionary<string,Rectangle>();
            foreach(string n in names) { layers[n]=new Bitmap(w,h); bounds[n]=Rectangle.Empty; }
            using(var target=new Bitmap(w,h)) using(var composed=new Bitmap(w,h)) {
                try {
                    for(int y=0;y<h;y++) for(int x=0;x<w;x++) {
                        Color c=src.GetPixel(x,y), m=matte.GetPixel(x,y);
                        int a=m.R<16?0:(m.R>239?255:(m.R-16)*255/224);
                        // The generated matte mistakes hair behind glasses for empty lenses.
                        // Restore enclosed source content and remove connected white backdrop spill.
                        if(Box(x,y,710,28,819,70) && !exterior[y*w+x]) a=255;
                        if(exterior[y*w+x]) a=0;
                        if(a==0) continue;
                        Color pixel=Color.FromArgb(a,c.R,c.G,c.B); target.SetPixel(x,y,pixel);
                        string n;
                        if(y<192 && x>665 && x<865) {
                            if(y>=172 && x>=744 && x<=787) n="neck";
                            else if(face.IsVisible(x,y)) n="face";
                            else if(y>140 && c.R>c.B*1.25 && (x<746 || x>785)) n="back_hair";
                            else if(x<740 && y>64) n="hair_left";
                            else if(x>789 && y>64) n="hair_right";
                            else n="hair_front";
                            if(Box(x,y,710,28,818,64) && Math.Max(c.R,Math.Max(c.G,c.B))<120) n="glasses";
                            if(Box(x,y,723,107,757,127)) n="eye_left";
                            if(Box(x,y,773,107,808,127)) n="eye_right";
                            if(Iris(x,y,742)) n="iris_left";
                            if(Iris(x,y,789)) n="iris_right";
                            if(Box(x,y,724,95,758,106)) n="brow_left";
                            if(Box(x,y,773,95,807,106)) n="brow_right";
                            if(Box(x,y,759,132,772,145)) n="nose";
                            if(Box(x,y,750,146,781,158)) n="mouth";
                        } else if(y>=538) n=x<765?"leg_left":"leg_right";
                        else if(y>=507) n="skirt";
                        else if(x<412) n="hand_left";
                        else if(x>1118) n="hand_right";
                        else if(x<654) n="sleeve_left";
                        else if(x>876) n="sleeve_right";
                        else n="torso";
                        layers[n].SetPixel(x,y,pixel);
                        var p=new Rectangle(x,y,1,1);
                        bounds[n]=bounds[n].IsEmpty?p:Rectangle.Union(bounds[n],p);
                        // Generated paint is fully hidden at rest by opaque source pixels.
                        if(a==255 && cleanRegion.IsVisible(x,y)) {
                            layers["skin_underpaint"].SetPixel(x,y,clean.GetPixel(x,y));
                            bounds["skin_underpaint"]=bounds["skin_underpaint"].IsEmpty?p:Rectangle.Union(bounds["skin_underpaint"],p);
                        }
                    }
                    var parts=new List<RegisteredPart>();
                    using(var g=Graphics.FromImage(composed)) {
                        foreach(string n in names) {
                            Rectangle b=bounds[n];
                            if(b.IsEmpty) throw new Exception("Empty layer: "+n);
                            using(var crop=layers[n].Clone(b,PixelFormat.Format32bppArgb)) {
                                crop.Save(Path.Combine(output,"parts",n+".png"),ImageFormat.Png);
                                g.DrawImageUnscaled(crop,b.Location);
                            }
                            parts.Add(new RegisteredPart{name=n,left=b.Left,top=b.Top,width=b.Width,height=b.Height});
                        }
                    }
                    changedPixels=0; sourceColorMismatches=0;
                    for(int y=0;y<h;y++) for(int x=0;x<w;x++) {
                        Color t=target.GetPixel(x,y),c=composed.GetPixel(x,y),s=src.GetPixel(x,y);
                        // GDI+ rounds RGB at partially transparent edges; compare opaque pixels exactly.
                        if(t.A==255 && t.ToArgb()!=c.ToArgb()) changedPixels++;
                        if(t.A==255 && (c.R!=s.R||c.G!=s.G||c.B!=s.B)) sourceColorMismatches++;
                        if(t.A!=c.A) throw new Exception("Layer alpha mismatch at "+x+","+y);
                    }
                    if(changedPixels!=0) throw new Exception("Recomposition changed opaque source pixels.");
                    target.Save(Path.Combine(output,"source-cutout.png"),ImageFormat.Png);
                    composed.Save(Path.Combine(output,"assembled-preview.png"),ImageFormat.Png);
                    using(var panel=new Bitmap(1260,460)) using(var g=Graphics.FromImage(panel))
                    using(var rejected=new Bitmap(Path.Combine(output,"..","source-measured","assembled-preview.png")))
                    using(var font=new Font("Arial",16)) {
                        g.Clear(Color.FromArgb(238,240,244));
                        g.InterpolationMode=InterpolationMode.NearestNeighbor;
                        var region=new Rectangle(660,0,210,210);
                        g.DrawImage(src,new Rectangle(0,40,420,420),region,GraphicsUnit.Pixel);
                        g.DrawImage(rejected,new Rectangle(420,40,420,420),region,GraphicsUnit.Pixel);
                        g.DrawImage(composed,new Rectangle(840,40,420,420),region,GraphicsUnit.Pixel);
                        g.DrawString("ORIGINAL",font,Brushes.Black,12,8);
                        g.DrawString("REJECTED",font,Brushes.Black,432,8);
                        g.DrawString("REGISTERED SOURCE LAYERS",font,Brushes.Black,852,8);
                        panel.Save(Path.Combine(output,"face-comparison.png"),ImageFormat.Png);
                    }
                    return parts.ToArray();
                } finally { foreach(var bmp in layers.Values) bmp.Dispose(); }
            }
        }
    }
}
'@
$parts=[BinaRegistered]::Build($source,(Join-Path $out 'matte-generated.png'),(Join-Path $out 'underpaint-generated.png'),$out)
$tagMap=@{
    skin_underpaint=@('face','base');torso=@('top');neck=@('neck');face=@('face')
    back_hair=@('hair','back');hair_front=@('hair','front');hair_left=@('hair','right');hair_right=@('hair','left')
    glasses=@('headwear');eye_left=@('eye','right');eye_right=@('eye','left')
    iris_left=@('eye','iris','right');iris_right=@('eye','iris','left')
    brow_left=@('brow','right');brow_right=@('brow','left');nose=@('nose');mouth=@('mouth')
    sleeve_left=@('arm','right');sleeve_right=@('arm','left');hand_left=@('hand','right');hand_right=@('hand','left')
    skirt=@('skirt');leg_left=@('leg','right');leg_right=@('leg','left')
}
$layers=@($parts | ForEach-Object {
    [ordered]@{id=$_.name;name=$_.name;tags=$tagMap[$_.name];image=@{path="parts/$($_.name).png";width=$_.width;height=$_.height};rect=@{left=$_.left;top=$_.top;width=$_.width;height=$_.height}}
})
$layout=[ordered]@{format='psd2live-layout';version=1;name='bina-registered';canvas=@{width=1536;height=1024};layers=$layers}
Write-Utf8Lf (Join-Path $out 'bina.layout.json') ($layout | ConvertTo-Json -Depth 10)
$report=[ordered]@{
    reference='assets/bina-tpose/casual/bina-casual-tpose-front.png';reference_sha256=$actual
    canvas=@(1536,1024);scale=1;layer_count=$parts.Count
    opaque_source_color_mismatches=[BinaRegistered]::sourceColorMismatches
    opaque_recomposition_mismatches=[BinaRegistered]::changedPixels
    alpha_recomposition='pass';coordinates='original pixels; integer crop offsets; no independent transforms'
    target_landmarks=$measure.views.'casual-front'.landmarks_px
    generated_edits=@('foreground matte','hidden face underpainting')
    matte_refinement='Source-connected white backdrop removed; enclosed original hair behind glasses restored.'
    status='static source fidelity verified; animation overlap and deformers not yet validated'
    limitations=@('Source head is 144 pixels tall; no invented high-resolution facial detail.',
        'Feature patches retain adjacent skin; hair and feature masks need animation-driven edge refinement.',
        'Hidden scalp/face paint supplied; sleeve, skirt and leg joints still need overlap painting before large motions.')
}
Write-Utf8Lf (Join-Path $out 'material-report.json') ($report | ConvertTo-Json -Depth 10)
Write-Output "Prepared $($parts.Count) registered layers; opaque source mismatches: $([BinaRegistered]::sourceColorMismatches)"

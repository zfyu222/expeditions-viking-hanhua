using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Security.Cryptography;
using Mono.Cecil;
using Mono.Cecil.Cil;

class PatchOverheadTiming
{
    const string Original = "c7b37f617f2e4561b939f02aebba5841ee87c554d8c5f43bf18887d362106af5";
    static string Hash(string p) { using(var s=File.OpenRead(p)) using(var h=SHA256.Create()) return BitConverter.ToString(h.ComputeHash(s)).Replace("-", "").ToLowerInvariant(); }
    static IEnumerable<TypeDefinition> Types(IEnumerable<TypeDefinition> ts) { foreach(var t in ts) { yield return t; foreach(var n in Types(t.NestedTypes)) yield return n; } }
    static Dictionary<string,string> Bodies(ModuleDefinition m) {
        return Types(m.Types).SelectMany(t=>t.Methods).Where(x=>x.HasBody).ToDictionary(x=>x.FullName,x=>String.Join("\n",x.Body.Instructions.Select(i=>i.ToString()).ToArray()));
    }
    static void Main(string[] a) { try { Run(a); } catch(Exception e) { Console.Error.WriteLine(e.GetType().FullName+": "+e.Message+"\n"+e.StackTrace); Environment.Exit(1); } }
    static void Run(string[] a)
    {
        if(a.Length!=4 || Hash(a[0])!=Original || File.Exists(a[2])) throw new Exception("Wrong original hash or output already exists");
        var resolver=new DefaultAssemblyResolver(); resolver.AddSearchDirectory(a[3]);
        var game=AssemblyDefinition.ReadAssembly(a[0],new ReaderParameters {AssemblyResolver=resolver}); var mod=game.MainModule;
        var before=Bodies(mod); var refs=mod.AssemblyReferences.Select(r=>r.FullName).ToArray();
        var target=mod.Types.Single(t=>t.FullName=="LAGUI.Widgets.OverheadPanel").Methods.Single(m=>m.Name=="SetText");
        var donor=AssemblyDefinition.ReadAssembly(a[1]).MainModule.Types.Single(t=>t.Name=="OverheadTiming").Methods.Single(m=>m.Name=="GetDisplaySeconds");
        var type=new TypeDefinition("ZFY", "OverheadTiming", TypeAttributes.Public|TypeAttributes.Abstract|TypeAttributes.Sealed,mod.TypeSystem.Object);
        mod.Types.Add(type);
        var method=new MethodDefinition(donor.Name,MethodAttributes.Public|MethodAttributes.Static,mod.TypeSystem.Single); type.Methods.Add(method);
        foreach(var p in donor.Parameters) method.Parameters.Add(new ParameterDefinition(p.Name,p.Attributes,mod.Import(p.ParameterType)));
        method.Body.InitLocals=donor.Body.InitLocals; method.Body.MaxStackSize=donor.Body.MaxStackSize;
        foreach(var v in donor.Body.Variables) method.Body.Variables.Add(new VariableDefinition(mod.Import(v.VariableType)));
        var map=new Dictionary<Instruction,Instruction>();
        foreach(var i in donor.Body.Instructions) { var n=Instruction.Create(OpCodes.Nop); n.OpCode=i.OpCode; method.Body.Instructions.Add(n); map.Add(i,n); }
        foreach(var i in donor.Body.Instructions) {
            object o=i.Operand;
            if(o is Instruction) o=map[(Instruction)o];
            else if(o is Instruction[]) o=((Instruction[])o).Select(j=>map[j]).ToArray();
            else if(o is MethodReference) o=mod.Import((MethodReference)o);
            else if(o is TypeReference) o=mod.Import((TypeReference)o);
            else if(o is FieldReference) o=mod.Import((FieldReference)o);
            else if(o is VariableDefinition) o=method.Body.Variables[donor.Body.Variables.IndexOf((VariableDefinition)o)];
            else if(o is ParameterDefinition) o=method.Parameters[donor.Parameters.IndexOf((ParameterDefinition)o)];
            map[i].Operand=o;
        }
        if(donor.Body.ExceptionHandlers.Count!=0) throw new Exception("Unexpected helper exception regions");
        var store=target.Body.Instructions.Single(i=>i.OpCode==OpCodes.Stfld && ((FieldReference)i.Operand).Name=="timeToDisplay");
        if(store.Previous.OpCode!=OpCodes.Mul) throw new Exception("Unexpected timer IL");
        var il=target.Body.GetILProcessor();
        il.InsertBefore(store,Instruction.Create(OpCodes.Ldarg_1));
        il.InsertBefore(store,Instruction.Create(OpCodes.Call,method));
        game.Write(a[2]);
        var result=AssemblyDefinition.ReadAssembly(a[2]).MainModule; var after=Bodies(result);
        var changed=before.Keys.Where(k=>before[k]!=after[k]).ToArray();
        if(changed.Length!=1 || changed[0]!=target.FullName || after.Count!=before.Count+1 || !refs.SequenceEqual(result.AssemblyReferences.Select(r=>r.FullName))) throw new Exception("Unexpected assembly changes");
        File.WriteAllLines(a[2]+".verification.txt",new[]{"original_sha256="+Original,"patched_sha256="+Hash(a[2]),"changed_existing_methods=1","added_methods=1","assembly_references_unchanged=true","changed_method="+target.FullName});
        Console.WriteLine("Verified: one timer call inserted; one helper added; all other method instructions and assembly references unchanged.");
    }
}

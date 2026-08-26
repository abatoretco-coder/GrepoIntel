import {NextRequest,NextResponse} from "next/server";

const backend=()=>process.env.INTERNAL_API_URL??"http://backend:8000";

export async function POST(request:NextRequest,{params}:{params:Promise<{action:string}>}){
  const {action}=await params;
  if(action!=="pairing"&&action!=="import")return NextResponse.json({detail:"Not found"},{status:404});
  const headers=new Headers({"Content-Type":"application/json"});
  const pairing=request.headers.get("X-GrepoIntel-Pairing");
  if(pairing)headers.set("X-GrepoIntel-Pairing",pairing);
  try{
    const response=await fetch(`${backend()}/api/personal-state/${action}`,{method:"POST",headers,body:action==="import"?await request.text():undefined,cache:"no-store"});
    return new NextResponse(await response.text(),{status:response.status,headers:{"Content-Type":response.headers.get("Content-Type")??"application/json"}});
  }catch{return NextResponse.json({detail:"Backend unavailable"},{status:503})}
}

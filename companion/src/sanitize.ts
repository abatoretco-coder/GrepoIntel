const forbidden=/(cookie|password|csrf|token|session|authorization|auth)/i;
export function sanitize(value:any):any {
  if(Array.isArray(value)) return value.map(sanitize);
  if(value&&typeof value==="object") return Object.fromEntries(Object.entries(value).filter(([key])=>!forbidden.test(key)).map(([key,item])=>[key,sanitize(item)]));
  return value;
}

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity, AlertCircle, AlertTriangle, ArrowDownRight, ArrowUpRight,
  Bell, Boxes, CalendarDays, Check, CheckCheck, ChevronDown, CircleHelp,
  Clock3, Command, LayoutDashboard, LoaderCircle, LogOut, Menu, Package,
  Plus, RefreshCw, Search, Settings2, ShieldCheck, ShoppingBasket,
  SlidersHorizontal, Store, Truck, X, Zap,
} from "lucide-react";
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import {
  adjustStock, createBatch, createProduct, createShelf, errorMessage,
  getAlerts, getBatches, getDashboard, getEvents, getInventory, getProducts,
  getShelves, markAlertRead, receiveStock, refreshAlerts, resolveAlert,
} from "./api";

const NAV = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "inventory", label: "Inventory", icon: Boxes },
  { id: "products", label: "Products", icon: Package },
  { id: "batches", label: "Batches & expiry", icon: CalendarDays },
  { id: "shelves", label: "Smart shelves", icon: Store },
  { id: "alerts", label: "Alerts centre", icon: Bell },
];
const money = value => new Intl.NumberFormat("en-US", { style: "currency", currency: "TND", maximumFractionDigits: 2 }).format(Number(value || 0));
const date = value => value ? new Date(value).toLocaleDateString() : "—";
const dateTime = value => value ? new Date(value).toLocaleString() : "—";
const titleCase = value => String(value || "").toLowerCase().replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase());

function App() {
  const [page, setPage] = useState("overview");
  const [summary, setSummary] = useState(null);
  const [inventory, setInventory] = useState([]);
  const [events, setEvents] = useState([]);
  const [products, setProducts] = useState([]);
  const [batches, setBatches] = useState([]);
  const [shelves, setShelves] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [modal, setModal] = useState("");
  const [selectedRow, setSelectedRow] = useState(null);
  const [toast, setToast] = useState("");

  const loadAll = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true); else setLoading(true);
    setError("");
    try {
      const [s, i, e, p, b, sh, a] = await Promise.all([
        getDashboard(), getInventory(), getEvents(), getProducts(),
        getBatches(), getShelves(), getAlerts(),
      ]);
      setSummary(s); setInventory(i); setEvents(e); setProducts(p);
      setBatches(b); setShelves(sh); setAlerts(a);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false); setRefreshing(false);
    }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);
  useEffect(() => {
    const timer = setInterval(() => loadAll(true), 30000);
    return () => clearInterval(timer);
  }, [loadAll]);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 3200);
    return () => clearTimeout(timer);
  }, [toast]);

  const notify = message => setToast(message);
  const runAction = async (action, message) => {
    try { await action(); await loadAll(true); notify(message); setModal(""); }
    catch (err) { setError(errorMessage(err)); }
  };

  const filteredInventory = useMemo(() => inventory.filter(x =>
    [x.product_name, x.batch_number, x.shelf_code].join(" ").toLowerCase().includes(query.toLowerCase())
  ), [inventory, query]);
  const filteredProducts = useMemo(() => products.filter(x =>
    [x.name, x.brand, x.barcode, x.sku].join(" ").toLowerCase().includes(query.toLowerCase())
  ), [products, query]);
  const filteredBatches = useMemo(() => batches.filter(x =>
    [x.batch_number, products.find(p => p.id === x.product_id)?.name].join(" ").toLowerCase().includes(query.toLowerCase())
  ), [batches, products, query]);
  const filteredShelves = useMemo(() => shelves.filter(x =>
    [x.code, x.name, x.location, x.device_id].join(" ").toLowerCase().includes(query.toLowerCase())
  ), [shelves, query]);

  const chartData = useMemo(() => {
    const days = new Map();
    events.forEach(event => {
      const key = new Date(event.occurred_at).toLocaleDateString(undefined, { month: "short", day: "numeric" });
      const row = days.get(key) || { day: key, purchases: 0, restocks: 0 };
      if (event.quantity_change < 0) row.purchases += Math.abs(event.quantity_change);
      if (event.quantity_change > 0) row.restocks += event.quantity_change;
      days.set(key, row);
    });
    return [...days.values()].slice(-8);
  }, [events]);

  const activeAlerts = alerts.filter(a => !a.is_resolved);
  const pageTitle = NAV.find(n => n.id === page)?.label || "Overview";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark"><Store size={20}/></div><div><strong>SMARTSHELF</strong><span>INVENTORY INTELLIGENCE</span></div></div>
        <div className="workspace-label">WORKSPACE</div>
        <nav className="nav-list">
          {NAV.map(item => <button key={item.id} className={`nav-item ${page === item.id ? "active" : ""}`} onClick={() => { setPage(item.id); setQuery(""); }}>
            <item.icon size={18}/><span>{item.label}</span>
            {item.id === "alerts" && activeAlerts.length > 0 && <em>{activeAlerts.length}</em>}
          </button>)}
        </nav>
        <div className="sidebar-bottom">
          <div className="server-card"><div className="server-status"><span className="pulse-dot"/> LOCAL SERVER</div><strong>SMARTSHELF node</strong><small>API · PostgreSQL · MQTT</small></div>
          <div className="profile"><div className="avatar">SS</div><div><strong>Store operator</strong><small>Administrator</small></div><ChevronDown size={15}/></div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb"><span>Workspace</span><b>/</b><strong>{pageTitle}</strong></div>
          <div className="top-actions">
            <div className="live-indicator"><span className="pulse-dot"/> Live data</div>
            <button className="icon-button" title="Refresh data" onClick={() => loadAll(true)} disabled={refreshing}>{refreshing ? <LoaderCircle className="spin" size={18}/> : <RefreshCw size={18}/>}</button>
            <button className="icon-button notification-button" title="Alerts" onClick={() => setPage("alerts")}><Bell size={18}/>{activeAlerts.length > 0 && <i/>}</button>
            <div className="top-avatar">A</div>
          </div>
        </header>

        <section className="content">
          {error && <div className="error-banner"><AlertCircle size={17}/><span>{error}</span><button onClick={() => setError("")}><X size={16}/></button></div>}
          {loading ? <div className="loading-state"><LoaderCircle className="spin" size={28}/><span>Connecting to SMARTSHELF services…</span></div> :
            <>
              {page === "overview" && <Overview summary={summary} inventory={inventory} events={events} alerts={activeAlerts} chartData={chartData} onNavigate={setPage} onRefreshAlerts={() => runAction(refreshAlerts, "Alerts refreshed")} />}
              {page === "inventory" && <InventoryPage rows={filteredInventory} query={query} setQuery={setQuery} onReceive={() => setModal("receive")} onAdjust={row => {setSelectedRow(row);setModal("adjust");}} />}
              {page === "products" && <ProductsPage rows={filteredProducts} query={query} setQuery={setQuery} onAdd={() => setModal("product")} />}
              {page === "batches" && <BatchesPage rows={filteredBatches} products={products} query={query} setQuery={setQuery} onAdd={() => setModal("batch")} />}
              {page === "shelves" && <ShelvesPage rows={filteredShelves} query={query} setQuery={setQuery} onAdd={() => setModal("shelf")} />}
              {page === "alerts" && <AlertsPage rows={alerts} onRead={id => runAction(() => markAlertRead(id), "Alert marked as read")} onResolve={id => runAction(() => resolveAlert(id), "Alert resolved")} onRefresh={() => runAction(refreshAlerts, "Alerts refreshed")} />}
            </>
          }
        </section>
        <footer className="footer"><span>SMARTSHELF · Smart inventory monitoring</span><span>Auto-refresh every 30 seconds <span className="footer-dot">·</span> API connected locally</span></footer>
      </main>

      {modal && <Modal title={{receive:"Receive stock",adjust:"Adjust stock",product:"Add product",batch:"Register batch",shelf:"Register smart shelf"}[modal]} onClose={() => setModal("")}>
        {modal === "receive" && <ReceiveForm batches={batches} shelves={shelves} onSubmit={data => runAction(() => receiveStock(data), "Stock received successfully")} onCancel={() => setModal("")} />}
        {modal === "adjust" && <AdjustForm row={selectedRow} onSubmit={data => runAction(() => adjustStock(selectedRow.id, data), "Inventory adjusted successfully")} onCancel={() => setModal("")} />}
        {modal === "product" && <ProductForm onSubmit={data => runAction(() => createProduct(data), "Product created successfully")} onCancel={() => setModal("")} />}
        {modal === "batch" && <BatchForm products={products} onSubmit={data => runAction(() => createBatch(data), "Batch registered successfully")} onCancel={() => setModal("")} />}
        {modal === "shelf" && <ShelfForm onSubmit={data => runAction(() => createShelf(data), "Shelf registered successfully")} onCancel={() => setModal("")} />}
      </Modal>}
      {toast && <div className="toast"><Check size={17}/>{toast}</div>}
    </div>
  );
}

function PageHeading({eyebrow, title, description, action}) {
  return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action}</div>;
}
function Metric({label, value, detail, icon: Icon, tone="green", trend}) {
  return <div className="metric-card"><div className="metric-top"><span>{label}</span><div className={`metric-icon ${tone}`}><Icon size={18}/></div></div><div className="metric-value">{value ?? "—"}</div><div className="metric-detail">{trend && <span className="metric-trend"><ArrowUpRight size={13}/>{trend}</span>}{detail}</div></div>;
}
function Overview({summary, inventory, events, alerts, chartData, onNavigate, onRefreshAlerts}) {
  const stockValue = inventory.reduce((sum, row) => sum + Number(row.quantity || 0), 0);
  return <>
    <PageHeading eyebrow="MONDAY, NOVEMBER 23" title="Good afternoon" description="Here’s what’s happening across your inventory today." action={<button className="button button-dark" onClick={onRefreshAlerts}><RefreshCw size={16}/> Refresh alerts</button>}/>
    <div className="metric-grid">
      <Metric label="Active products" value={summary?.total_products ?? 0} detail="Registered in catalogue" icon={Package} tone="blue"/>
      <Metric label="Units in stock" value={summary?.total_stock_units ?? stockValue} detail="Across all active shelves" icon={Boxes} tone="green"/>
      <Metric label="Low / out of stock" value={(summary?.low_stock_products || 0) + (summary?.out_of_stock_products || 0)} detail={`${summary?.low_stock_products || 0} low · ${summary?.out_of_stock_products || 0} out of stock`} icon={ShoppingBasket} tone="orange"/>
      <Metric label="Expiry attention" value={(summary?.expiring_batches || 0) + (summary?.batches_expiring_today || 0) + (summary?.expired_batches || 0)} detail={`${summary?.expired_batches || 0} expired batches`} icon={CalendarDays} tone="red"/>
    </div>
    <div className="overview-grid">
      <section className="panel chart-panel"><div className="panel-heading"><div><h2>Inventory movement</h2><p>Units sold and restocked · based on recorded events</p></div><span className="period-pill"><Activity size={14}/> Event history</span></div>
        {chartData.length ? <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData} margin={{top:10,right:8,left:-18,bottom:0}}><defs><linearGradient id="purchaseFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#e69b55" stopOpacity={0.2}/><stop offset="100%" stopColor="#e69b55" stopOpacity={0}/></linearGradient><linearGradient id="restockFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#2e8b70" stopOpacity={0.2}/><stop offset="100%" stopColor="#2e8b70" stopOpacity={0}/></linearGradient></defs><CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#edf0ee"/><XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fill:"#8b9690",fontSize:11}}/><YAxis axisLine={false} tickLine={false} tick={{fill:"#8b9690",fontSize:11}}/><Tooltip contentStyle={{border:"1px solid #e8eeea",borderRadius:12,fontSize:12}}/><Area type="monotone" dataKey="purchases" name="Units sold" stroke="#d88a43" strokeWidth={2.5} fill="url(#purchaseFill)"/><Area type="monotone" dataKey="restocks" name="Units restocked" stroke="#2e8b70" strokeWidth={2.5} fill="url(#restockFill)"/></AreaChart></ResponsiveContainer></div> : <Empty icon={Activity} title="No movement recorded yet" text="Inventory events will appear here after stock changes are registered."/>}
        <div className="chart-legend"><span><i className="legend-dot amber"/> Units sold</span><span><i className="legend-dot green"/> Units restocked</span></div>
      </section>
      <section className="panel alert-panel"><div className="panel-heading"><div><h2>Attention required</h2><p>Open inventory alerts</p></div><button className="text-button" onClick={() => onNavigate("alerts")}>View all <ArrowUpRight size={14}/></button></div>
        {alerts.length ? <div className="alert-preview-list">{alerts.slice(0,5).map(a => <div className="alert-preview" key={a.id}><div className={`alert-symbol ${a.priority?.toLowerCase()}`}><AlertTriangle size={16}/></div><div className="alert-preview-copy"><strong>{a.title}</strong><span>{a.message}</span><small>{dateTime(a.created_at)}</small></div><span className={`priority ${a.priority?.toLowerCase()}`}>{titleCase(a.priority)}</span></div>)}</div> : <Empty icon={ShieldCheck} title="All clear" text="There are no unresolved alerts at the moment."/>}
      </section>
    </div>
    <div className="lower-grid">
      <section className="panel"><div className="panel-heading"><div><h2>Stock by shelf</h2><p>Current quantities across your locations</p></div><button className="text-button" onClick={() => onNavigate("inventory")}>Inventory <ArrowUpRight size={14}/></button></div>
        {inventory.length ? <div className="compact-table"><div className="table-head"><span>PRODUCT / BATCH</span><span>SHELF</span><span>QUANTITY</span></div>{inventory.slice(0,5).map(row => <div className="table-row" key={row.id}><div className="product-cell"><div className="product-thumb"><Package size={17}/></div><div><strong>{row.product_name}</strong><small>{row.batch_number}</small></div></div><span className="shelf-tag">{row.shelf_code}</span><strong className="quantity">{row.quantity}</strong></div>)}</div> : <Empty icon={Boxes} title="No inventory records" text="Receive stock to populate your inventory."/>}
      </section>
      <section className="panel activity-panel"><div className="panel-heading"><div><h2>Recent activity</h2><p>Latest stock events</p></div><button className="text-button" onClick={() => onNavigate("inventory")}>See inventory</button></div>
        {events.length ? <div className="activity-list">{events.slice(0,5).map(e => <div className="activity-item" key={e.id}><div className={`activity-icon ${e.quantity_change > 0 ? "positive" : "negative"}`}>{e.quantity_change > 0 ? <ArrowDownRight size={16}/> : <ArrowUpRight size={16}/>}</div><div><strong>{e.event_type === "SIMULATED" ? "Shelf movement" : titleCase(e.event_type)}</strong><span>{e.quantity_change > 0 ? "+" : ""}{e.quantity_change} units · {titleCase(e.source)}</span></div><time>{dateTime(e.occurred_at)}</time></div>)}</div> : <Empty icon={Clock3} title="No recent activity" text="Recorded stock events will show here."/>}
      </section>
    </div>
  </>;
}
function SearchBar({value,onChange,placeholder="Search..."}) { return <label className="search-box"><Search size={17}/><input value={value} onChange={e=>onChange(e.target.value)} placeholder={placeholder}/>{value && <button onClick={()=>onChange("")}><X size={14}/></button>}</label>; }
function TablePanel({children,empty}) { return <div className="panel table-panel">{children || <Empty icon={Boxes} title={empty || "Nothing here yet"} text="Records will appear here when available."/>}</div>; }
function InventoryPage({rows,query,setQuery,onReceive,onAdjust}) {
  return <><PageHeading eyebrow="STOCK CONTROL" title="Inventory" description="Monitor quantities by product, batch and smart shelf." action={<button className="button button-dark" onClick={onReceive}><Plus size={16}/> Receive stock</button>}/>
    <div className="toolbar"><SearchBar value={query} onChange={setQuery} placeholder="Search product, batch or shelf"/><span className="result-count">{rows.length} inventory records</span></div>
    <TablePanel empty="No inventory records"><div className="data-table"><div className="data-head inv-cols"><span>PRODUCT</span><span>BATCH / EXPIRY</span><span>SHELF</span><span>QUANTITY</span><span>UPDATED</span><span/></div>{rows.map(r=><div className="data-row inv-cols" key={r.id}><div className="product-cell"><div className="product-thumb"><Package size={17}/></div><div><strong>{r.product_name}</strong><small>Product #{r.product_id}</small></div></div><div><strong>{r.batch_number}</strong><small>Batch #{r.batch_id}</small></div><div><span className="shelf-tag">{r.shelf_code}</span><small>{r.shelf_name}</small></div><strong className="quantity">{r.quantity} units</strong><span className="muted">{date(r.updated_at)}</span><button className="small-action" onClick={()=>onAdjust(r)}>Adjust</button></div>)}</div></TablePanel>
  </>;
}
function ProductsPage({rows,query,setQuery,onAdd}) {
  return <><PageHeading eyebrow="CATALOGUE" title="Products" description="Manage product information, barcodes, pricing and stock thresholds." action={<button className="button button-dark" onClick={onAdd}><Plus size={16}/> Add product</button>}/><div className="toolbar"><SearchBar value={query} onChange={setQuery} placeholder="Search name, brand, SKU or barcode"/><span className="result-count">{rows.length} products</span></div><TablePanel empty="No products found"><div className="data-table"><div className="data-head product-cols"><span>PRODUCT</span><span>BARCODE / SKU</span><span>CATEGORY ID</span><span>SELLING PRICE</span><span>MIN STOCK</span><span>STATUS</span></div>{rows.map(p=><div className="data-row product-cols" key={p.id}><div className="product-cell"><div className="product-thumb"><Package size={17}/></div><div><strong>{p.name}</strong><small>{p.brand || "No brand specified"}</small></div></div><div><strong>{p.barcode || "—"}</strong><small>{p.sku || "No SKU"}</small></div><span>{p.category_id ?? "—"}</span><strong>{money(p.selling_price)}</strong><span>{p.min_stock}</span><span className={`status-pill ${p.is_active ? "ok" : "off"}`}>{p.is_active ? "Active" : "Inactive"}</span></div>)}</div></TablePanel></>;
}
function BatchesPage({rows,products,query,setQuery,onAdd}) {
  return <><PageHeading eyebrow="TRACEABILITY" title="Batches & expiry" description="Track product batches and their expiration dates." action={<button className="button button-dark" onClick={onAdd}><Plus size={16}/> Register batch</button>}/><div className="toolbar"><SearchBar value={query} onChange={setQuery} placeholder="Search batch or product"/><span className="result-count">{rows.length} batches</span></div><TablePanel empty="No batches registered"><div className="data-table"><div className="data-head batch-cols"><span>BATCH NUMBER</span><span>PRODUCT</span><span>EXPIRATION DATE</span><span>RECEIVED QTY</span><span>UNIT COST</span><span>REGISTERED</span></div>{rows.map(b=>{const expired=new Date(b.expiration_date)<new Date(new Date().toDateString());return <div className="data-row batch-cols" key={b.id}><strong>{b.batch_number}</strong><span>{products.find(p=>p.id===b.product_id)?.name || `Product #${b.product_id}`}</span><span className={expired?"danger-text":""}>{date(b.expiration_date)} {expired && <small>Expired</small>}</span><span>{b.received_quantity}</span><span>{b.purchase_price==null?"—":money(b.purchase_price)}</span><span className="muted">{date(b.received_at)}</span></div>})}</div></TablePanel></>;
}
function ShelvesPage({rows,query,setQuery,onAdd}) {
  return <><PageHeading eyebrow="IOT INFRASTRUCTURE" title="Smart shelves" description="Manage connected shelf identities and device status." action={<button className="button button-dark" onClick={onAdd}><Plus size={16}/> Add shelf</button>}/><div className="toolbar"><SearchBar value={query} onChange={setQuery} placeholder="Search shelf or device ID"/><span className="result-count">{rows.length} shelves</span></div><div className="shelf-grid">{rows.map(s=><div className="panel shelf-card" key={s.id}><div className="shelf-card-top"><div className="shelf-large-icon"><Store size={22}/></div><span className={`status-pill ${s.is_active?"ok":"off"}`}>{s.is_active?"Active":"Inactive"}</span></div><h3>{s.name}</h3><span className="shelf-code">{s.code}</span><div className="shelf-meta"><span><Zap size={14}/> {s.device_id || "No device ID"}</span><span><Activity size={14}/> {s.location || "Location not set"}</span></div></div>)}</div>{!rows.length&&<div className="panel"><Empty icon={Store} title="No shelves registered" text="Add a shelf to connect a simulated or physical device."/></div>}</>;
}
function AlertsPage({rows,onRead,onResolve,onRefresh}) {
  const [filter,setFilter]=useState("all");
  const visible=rows.filter(a=>filter==="all"?!a.is_resolved:filter==="unread"?!a.is_read&&!a.is_resolved:!a.is_resolved&&a.priority==="CRITICAL");
  return <><PageHeading eyebrow="RISK & EXCEPTIONS" title="Alerts centre" description="Review stock and expiration conditions requiring attention." action={<button className="button button-dark" onClick={onRefresh}><RefreshCw size={16}/> Recalculate alerts</button>}/><div className="filter-tabs">{[["all","All open"],["unread","Unread"],["critical","Critical"]].map(([v,l])=><button className={filter===v?"selected":""} key={v} onClick={()=>setFilter(v)}>{l}</button>)}</div><div className="alert-full-list">{visible.map(a=><div className="panel alert-card" key={a.id}><div className={`alert-symbol ${a.priority?.toLowerCase()}`}><AlertTriangle size={18}/></div><div className="alert-card-content"><div className="alert-title-row"><h3>{a.title}</h3><span className={`priority ${a.priority?.toLowerCase()}`}>{titleCase(a.priority)}</span></div><p>{a.message}</p><div className="alert-meta"><span>{titleCase(a.alert_type)}</span><span>·</span><span>{dateTime(a.created_at)}</span><span>·</span><span>{a.is_read?"Read":"Unread"}</span></div></div><div className="alert-actions">{!a.is_read&&<button className="button button-light" onClick={()=>onRead(a.id)}><Check size={15}/> Mark read</button>}<button className="button button-outline" onClick={()=>onResolve(a.id)}><CheckCheck size={15}/> Resolve</button></div></div>)}{!visible.length&&<div className="panel"><Empty icon={ShieldCheck} title="Nothing needs your attention" text="No alerts match this filter."/></div>}</div></>;
}
function Empty({icon:Icon,title,text}) { return <div className="empty-state"><div><Icon size={22}/></div><strong>{title}</strong><span>{text}</span></div>; }
function Modal({title,onClose,children}) { return <div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)onClose();}}><div className="modal"><div className="modal-heading"><div><span className="eyebrow">SMARTSHELF ACTION</span><h2>{title}</h2></div><button className="icon-button" onClick={onClose}><X size={18}/></button></div>{children}</div></div>; }
function FormField({label,children}) { return <label className="form-field"><span>{label}</span>{children}</label>; }
function FormActions({onCancel}) { return <div className="form-actions"><button type="button" className="button button-light" onClick={onCancel}>Cancel</button><button className="button button-dark" type="submit"><Check size={15}/> Save changes</button></div>; }
function ReceiveForm({batches,shelves,onSubmit,onCancel}) { const [batch,setBatch]=useState(batches[0]?.id||"");const [shelf,setShelf]=useState(shelves.find(s=>s.is_active)?.id||"");const [qty,setQty]=useState(1);const [notes,setNotes]=useState("");return <form onSubmit={e=>{e.preventDefault();onSubmit({batch_id:Number(batch),shelf_id:Number(shelf),quantity:Number(qty),notes:notes||null});}}><div className="form-grid"><FormField label="Product batch"><select required value={batch} onChange={e=>setBatch(e.target.value)}>{batches.map(b=><option key={b.id} value={b.id}>{b.batch_number} · Product #{b.product_id}</option>)}</select></FormField><FormField label="Destination shelf"><select required value={shelf} onChange={e=>setShelf(e.target.value)}>{shelves.filter(s=>s.is_active).map(s=><option key={s.id} value={s.id}>{s.code} · {s.name}</option>)}</select></FormField><FormField label="Quantity to receive"><input type="number" min="1" required value={qty} onChange={e=>setQty(e.target.value)}/></FormField><FormField label="Notes"><input value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Optional reference"/></FormField></div><FormActions onCancel={onCancel}/></form>; }
function AdjustForm({row,onSubmit,onCancel}) { const [qty,setQty]=useState(row?.quantity??0);const [notes,setNotes]=useState("");return <form onSubmit={e=>{e.preventDefault();onSubmit({new_quantity:Number(qty),notes:notes||null});}}><div className="context-note">Adjusting <strong>{row?.product_name}</strong> on <strong>{row?.shelf_code}</strong>. Current quantity: {row?.quantity}.</div><div className="form-grid"><FormField label="New quantity"><input type="number" min="0" required value={qty} onChange={e=>setQty(e.target.value)}/></FormField><FormField label="Reason / notes"><input value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Optional explanation"/></FormField></div><FormActions onCancel={onCancel}/></form>; }
function ProductForm({onSubmit,onCancel}) { const [v,setV]=useState({name:"",barcode:"",sku:"",brand:"",unit:"piece",selling_price:0,purchase_price:0,min_stock:0});const change=e=>setV({...v,[e.target.name]:e.target.type==="number"?Number(e.target.value):e.target.value});return <form onSubmit={e=>{e.preventDefault();onSubmit({...v,barcode:v.barcode||null,sku:v.sku||null,brand:v.brand||null});}}><div className="form-grid"><FormField label="Product name"><input name="name" required value={v.name} onChange={change}/></FormField><FormField label="Barcode"><input name="barcode" value={v.barcode} onChange={change}/></FormField><FormField label="SKU"><input name="sku" value={v.sku} onChange={change}/></FormField><FormField label="Brand"><input name="brand" value={v.brand} onChange={change}/></FormField><FormField label="Unit"><input name="unit" value={v.unit} onChange={change}/></FormField><FormField label="Selling price (TND)"><input name="selling_price" type="number" min="0" step="0.001" value={v.selling_price} onChange={change}/></FormField><FormField label="Purchase price (TND)"><input name="purchase_price" type="number" min="0" step="0.001" value={v.purchase_price} onChange={change}/></FormField><FormField label="Minimum stock"><input name="min_stock" type="number" min="0" value={v.min_stock} onChange={change}/></FormField></div><FormActions onCancel={onCancel}/></form>; }
function BatchForm({products,onSubmit,onCancel}) { const [v,setV]=useState({product_id:products[0]?.id||"",batch_number:"",expiration_date:"",received_quantity:1,purchase_price:""});const change=e=>setV({...v,[e.target.name]:e.target.value});return <form onSubmit={e=>{e.preventDefault();onSubmit({...v,product_id:Number(v.product_id),received_quantity:Number(v.received_quantity),purchase_price:v.purchase_price===""?null:Number(v.purchase_price)});}}><div className="form-grid"><FormField label="Product"><select name="product_id" value={v.product_id} onChange={change}>{products.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></FormField><FormField label="Batch number"><input name="batch_number" required value={v.batch_number} onChange={change}/></FormField><FormField label="Expiration date"><input type="date" name="expiration_date" required value={v.expiration_date} onChange={change}/></FormField><FormField label="Received quantity"><input type="number" min="1" name="received_quantity" required value={v.received_quantity} onChange={change}/></FormField><FormField label="Purchase price (TND)"><input type="number" min="0" step="0.001" name="purchase_price" value={v.purchase_price} onChange={change}/></FormField></div><FormActions onCancel={onCancel}/></form>; }
function ShelfForm({onSubmit,onCancel}) { const [v,setV]=useState({code:"",name:"",device_id:"",location:"",description:""});const change=e=>setV({...v,[e.target.name]:e.target.value});return <form onSubmit={e=>{e.preventDefault();onSubmit({...v,device_id:v.device_id||null,location:v.location||null,description:v.description||null});}}><div className="form-grid"><FormField label="Shelf code"><input name="code" required value={v.code} onChange={change} placeholder="SHELF-A02"/></FormField><FormField label="Shelf name"><input name="name" required value={v.name} onChange={change}/></FormField><FormField label="Device ID"><input name="device_id" value={v.device_id} onChange={change} placeholder="SIM-SHELF-002"/></FormField><FormField label="Location"><input name="location" value={v.location} onChange={change}/></FormField><FormField label="Description"><input name="description" value={v.description} onChange={change}/></FormField></div><FormActions onCancel={onCancel}/></form>; }

export default App;

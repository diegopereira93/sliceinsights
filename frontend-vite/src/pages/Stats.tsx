import { useGetMarketStats, useGetBrandStats } from "../lib/api-client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ScatterChart, Scatter, ZAxis, CartesianGrid } from "recharts";
import { TrendingUp, Database, Award, Activity } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

export default function Stats() {
  const { data: marketStats, isLoading: marketLoading } = useGetMarketStats();
  const { data: brandStats, isLoading: brandLoading } = useGetBrandStats();

  if (marketLoading || brandLoading) {
    return <div className="min-h-screen flex items-center justify-center text-primary font-mono">CARREGANDO TERMINAL...</div>;
  }

  if (!marketStats || !brandStats) return null;

  return (
    <div className="min-h-screen pt-8 pb-32 px-4 container mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-display font-black text-white italic tracking-wide">RAIO-X DO MERCADO</h1>
        <p className="text-zinc-400 font-mono text-xs mt-1">REAL-TIME DATA TERMINAL v1.0</p>
      </div>

      {/* Top KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard 
          title="TOTAL DB" 
          value={marketStats.totalPaddles.toString()} 
          icon={Database} 
        />
        <StatCard 
          title="PREÇO MÉDIO" 
          value={formatCurrency(marketStats.averagePrice)} 
          icon={TrendingUp} 
        />
        <StatCard 
          title="MELHOR CUSTO-BENEFÍCIO" 
          value={marketStats.bestValue?.name || "N/A"} 
          subValue={marketStats.bestValue?.brand}
          icon={Award} 
          highlight
        />
        <StatCard 
          title="MÁXIMA POTÊNCIA" 
          value={marketStats.topPower?.name || "N/A"} 
          subValue={marketStats.topPower?.brand}
          icon={Activity} 
        />
      </div>

      {/* Insight Banner */}
      {marketStats.marketInsight && (
        <div className="glass-panel p-4 rounded-xl border-primary/30 bg-primary/5 flex items-start gap-4 mb-8">
          <div className="p-2 bg-primary text-black rounded-lg mt-1">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-primary font-bold text-sm uppercase tracking-wider mb-1">MERCADO INSIGHT</h4>
            <p className="text-zinc-300">{marketStats.marketInsight}</p>
          </div>
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        
        {/* Brand Market Share Chart */}
        <div className="glass-card p-6 rounded-2xl">
          <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-6">Market Share por Marca (%)</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={brandStats} layout="vertical" margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                <XAxis type="number" hide />
                <YAxis dataKey="brand" type="category" axisLine={false} tickLine={false} tick={{fill: '#a1a1aa', fontSize: 12}} width={80} />
                <Tooltip 
                  cursor={{fill: 'rgba(255,255,255,0.05)'}}
                  contentStyle={{ backgroundColor: '#18181b', borderColor: '#3f3f46', borderRadius: '8px' }}
                  itemStyle={{ color: '#a3e635' }}
                />
                <Bar dataKey="marketShare" fill="#a3e635" radius={[0, 4, 4, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Power vs Control Scatter */}
        <div className="glass-card p-6 rounded-2xl">
          <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-6">Poder vs Controle</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis type="number" dataKey="control" name="Controle" domain={['dataMin - 5', 'dataMax + 5']} stroke="#71717a" tick={{fill: '#71717a', fontSize: 12}} />
                <YAxis type="number" dataKey="power" name="Poder" domain={['dataMin - 5', 'dataMax + 5']} stroke="#71717a" tick={{fill: '#71717a', fontSize: 12}} />
                <ZAxis type="number" range={[50, 400]} />
                <Tooltip cursor={{strokeDasharray: '3 3'}} content={<CustomScatterTooltip />} />
                <Scatter name="Raquetes" data={marketStats.powerVsControlData} fill="#3b82f6" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, subValue, icon: Icon, highlight = false }: any) {
  return (
    <div className={`p-5 rounded-2xl border ${highlight ? 'bg-primary/10 border-primary/30' : 'bg-zinc-900 border-white/5'}`}>
      <div className="flex justify-between items-start mb-4">
        <p className={`text-[10px] font-bold uppercase tracking-widest ${highlight ? 'text-primary' : 'text-zinc-500'}`}>{title}</p>
        <Icon className={`w-4 h-4 ${highlight ? 'text-primary' : 'text-zinc-600'}`} />
      </div>
      <p className="text-xl md:text-2xl font-bold text-white leading-tight truncate">{value}</p>
      {subValue && <p className="text-xs text-zinc-400 mt-1">{subValue}</p>}
    </div>
  );
}

const CustomScatterTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-zinc-900 border border-zinc-700 p-3 rounded-lg shadow-xl">
        <p className="text-white font-bold text-sm mb-1">{data.name}</p>
        <p className="text-primary text-xs uppercase mb-2">{data.brand}</p>
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div><span className="text-zinc-500">Poder:</span> <span className="text-white">{data.power}</span></div>
          <div><span className="text-zinc-500">Controle:</span> <span className="text-white">{data.control}</span></div>
        </div>
      </div>
    );
  }
  return null;
};

import { motion } from 'motion/react';
import { Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { RecommendationView } from '../api/mappers';

interface ResourcesProps {
  recommendations: RecommendationView[];
  loading: boolean;
  error: string;
}

export function Resources({ recommendations, loading, error }: ResourcesProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) {
      return recommendations;
    }
    return recommendations.filter(
      (r) =>
        r.title.toLowerCase().includes(query) ||
        r.description.toLowerCase().includes(query) ||
        r.direction.toLowerCase().includes(query),
    );
  }, [recommendations, searchQuery]);

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="mb-2">Tavsiyalar</h1>
        <p className="text-muted-foreground">`/recommendations/my/` endpoint bilan real integratsiya</p>
      </div>

      {/* Search and Filters */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="mb-8 space-y-4"
      >
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Resurslarni qidirish..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 rounded-xl bg-card border border-border focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </motion.div>

      {loading && <div className="rounded-xl border border-border p-4">Tavsiyalar yuklanmoqda...</div>}
      {!!error && <div className="rounded-xl border border-red-300 bg-red-50 p-4 text-red-600">{error}</div>}

      {!loading && !error && filtered.length === 0 && (
        <div className="rounded-xl border border-border p-4 text-muted-foreground">Mos tavsiya topilmadi.</div>
      )}

      {/* Resources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((item, index) => (
          <article key={`${item.title}-${index}`} className="rounded-xl border border-border p-4 space-y-2">
            <h3>{item.title}</h3>
            <p className="text-sm text-muted-foreground">{item.description || 'Tavsif mavjud emas'}</p>
            <div className="text-xs text-muted-foreground">
              <p>Direction: {item.direction}</p>
              <p>English: {item.minEnglishLevel} - {item.maxEnglishLevel}</p>
              <p>Type: {item.resourceType}</p>
              <p>Priority: {item.priority}</p>
            </div>
            <a href={item.url} target="_blank" rel="noreferrer" className="inline-block text-sm text-primary underline">
              Ochish
            </a>
          </article>
        ))}
      </div>
    </div>
  );
}

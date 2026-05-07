import Button from '@/components/Button';

export default function HelpSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-bold text-txt mb-4">About MythosEngine</h3>
        <div className="space-y-4 text-txt-secondary">
          <p>
            MythosEngine is a powerful world-building and campaign management tool
            designed for game masters and creative writers.
          </p>
          <p>Version: 1.0.0</p>
        </div>
      </div>

      <div className="border-t border-txt-muted/20 pt-6">
        <h3 className="text-lg font-bold text-txt mb-4">Resources</h3>
        <div className="space-y-2">
          <Button variant="secondary" className="w-full justify-start" onClick={() => window.open('https://github.com/MythosEngine/docs', '_blank')}>
            📖 Documentation
          </Button>
          <Button variant="secondary" className="w-full justify-start" onClick={() => window.open('https://discord.gg/mythosengine', '_blank')}>
            💬 Community Discord
          </Button>
          <Button variant="secondary" className="w-full justify-start" onClick={() => window.open('https://github.com/MythosEngine/issues', '_blank')}>
            🐛 Report Issue
          </Button>
        </div>
      </div>
    </div>
  );
}

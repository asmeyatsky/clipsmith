'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { X, DollarSign } from 'lucide-react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { videoService } from '@/lib/api/video'; // Assuming a tip function will be added here

interface TipModalProps {
    creatorId: string;
    videoId: string;
    isOpen: boolean;
    onClose: () => void;
}

export function TipModal({ creatorId, videoId, isOpen, onClose }: TipModalProps) {
    const [amount, setAmount] = useState<number | ''>(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleTip = async () => {
        if (!amount || amount <= 0) {
            setError("Please enter a valid tip amount.");
            return;
        }
        setLoading(true);
        setError(null);

        try {
            await videoService.sendTip(videoId, creatorId, amount as number); // Assuming sendTip function
            alert(`Successfully sent $${amount} tip!`);
            onClose();
        } catch (err: any) {
            setError(err.message || "Failed to send tip.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[425px] border-none bg-white dark:bg-zinc-950 p-0 overflow-hidden rounded-[2rem] shadow-2xl">
                <div className="bg-gradient-to-br from-purple-600 to-pink-600 p-8 text-white relative">
                    <DialogHeader>
                        <DialogTitle className="text-2xl font-black tracking-tight">Send a Tip</DialogTitle>
                    </DialogHeader>
                    <p className="text-purple-100 text-sm mt-2 font-medium opacity-80">Support the creator!</p>
                    <div className="absolute top-8 right-8 w-16 h-16 bg-white/10 rounded-full blur-2xl pointer-events-none" />
                </div>

                <div className="p-8 space-y-6">
                    {error && (
                        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500 text-sm text-center">
                            {error}
                        </div>
                    )}
                    <div className="space-y-2">
                        <label htmlFor="amount" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Tip Amount (USD)
                        </label>
                        <Input
                            id="amount"
                            type="number"
                            value={amount}
                            onChange={(e) => setAmount(parseFloat(e.target.value) || '')}
                            placeholder="e.g., 5.00"
                            min="0.01"
                            step="0.01"
                            className="h-12 rounded-xl bg-zinc-50 dark:bg-zinc-900 border-none ring-1 ring-zinc-200 dark:ring-zinc-800 focus-visible:ring-2 focus-visible:ring-purple-500"
                            disabled={loading}
                        />
                    </div>
                </div>

                <DialogFooter className="p-8 pt-0">
                    <Button
                        type="button"
                        onClick={handleTip}
                        disabled={loading || !amount || amount <= 0}
                        className="w-full h-12 rounded-full font-bold text-lg bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all"
                    >
                        {loading ? (
                            <>
                                <DollarSign size={20} className="animate-spin mr-2" />
                                Sending...
                            </>
                        ) : (
                            <>
                                <DollarSign size={20} className="mr-2" />
                                Send Tip
                            </>
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

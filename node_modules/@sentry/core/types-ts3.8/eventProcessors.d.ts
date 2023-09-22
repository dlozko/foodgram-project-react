import { Event, EventHint, EventProcessor } from '@sentry/types';
/**
 * Returns the global event processors.
 */
export declare function getGlobalEventProcessors(): EventProcessor[];
/**
 * Add a EventProcessor to be kept globally.
 * @param callback EventProcessor to add
 */
export declare function addGlobalEventProcessor(callback: EventProcessor): void;
/**
 * Process an array of event processors, returning the processed event (or `null` if the event was dropped).
 */
export declare function notifyEventProcessors(processors: EventProcessor[], event: Event | null, hint: EventHint, index?: number): PromiseLike<Event | null>;
//# sourceMappingURL=eventProcessors.d.ts.map
